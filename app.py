"""Flask application for YouTube video summarization and mindmap generation."""

import os
import re

from flask import Flask, jsonify, render_template, request
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from mindmap import generate_mindmap
from summarizer import summarize

app = Flask(__name__)
ENGLISH_TRANSCRIPT_LANGUAGES = ("en", "en-US", "en-GB")


def extract_video_id(url):
    """Extract YouTube video ID from various URL formats.

    Args:
        url: A YouTube video URL string.

    Returns:
        The video ID string, or None if not found.
    """
    patterns = [
        r'(?:v=|\/v\/|youtu\.be\/|\/embed\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


@app.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")


def fetch_video_transcript(video_id):
    """Fetch a transcript, trying multiple fallback strategies when needed."""
    ytt_api = YouTubeTranscriptApi()
    last_error = None

    try:
        return ytt_api.fetch(video_id, languages=ENGLISH_TRANSCRIPT_LANGUAGES)
    except Exception as exc:
        last_error = exc

    transcript_list = ytt_api.list(video_id)
    available_transcripts = list(transcript_list)

    candidates = []

    try:
        candidates.append(transcript_list.find_transcript(ENGLISH_TRANSCRIPT_LANGUAGES))
    except Exception:
        pass

    for transcript in available_transcripts:
        if transcript not in candidates:
            candidates.append(transcript)

    for transcript in candidates:
        fetch_targets = [transcript]

        if getattr(transcript, "language_code", None) != "en":
            try:
                fetch_targets.insert(0, transcript.translate("en"))
            except Exception as exc:
                last_error = exc

        for fetch_target in fetch_targets:
            try:
                return fetch_target.fetch()
            except Exception as exc:
                last_error = exc

    if last_error is not None:
        raise last_error

    raise RuntimeError("No transcript candidates were available.")


def build_transcript_error(error):
    """Create a user-facing error message for transcript retrieval failures."""
    error_name = type(error).__name__
    app.logger.warning("Transcript retrieval failed: %s", error, exc_info=error)

    if error_name in {"RequestBlocked", "IpBlocked", "YouTubeRequestFailed", "HTTPError"}:
        message = (
            "Could not reach YouTube to retrieve the transcript right now. "
            "If you're deploying on Render, YouTube may be blocking the server IP. "
            "Try again later or use a proxy/cookies-enabled deployment."
        )
        return jsonify({"error": message}), 503

    if error_name in {"ConnectionError", "Timeout", "ReadTimeout"}:
        message = (
            "Could not connect to YouTube to retrieve the transcript. "
            "Please try again in a moment."
        )
        return jsonify({"error": message}), 503

    return jsonify({
        "error": "Could not retrieve transcript for this video. "
                 "The video may not have captions available."
    }), 400


@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    """API endpoint to summarize a YouTube video and generate a mindmap.

    Expects JSON body with a "url" field containing a YouTube video URL.

    Returns:
        JSON with summary text and mindmap data, or an error message.
    """
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Please provide a YouTube video URL."}), 400

    url = data["url"].strip()
    if not url:
        return jsonify({"error": "Please provide a YouTube video URL."}), 400

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL. Please check and try again."}), 400

    try:
        transcript = fetch_video_transcript(video_id)
        formatter = TextFormatter()
        full_text = formatter.format_transcript(transcript)
    except Exception as exc:
        return build_transcript_error(exc)

    if not full_text.strip():
        return jsonify({"error": "Transcript is empty for this video."}), 400

    num_sentences = min(10, max(3, len(full_text) // 500))
    summary = summarize(full_text, num_sentences=num_sentences)

    video_title = f"Video {video_id}"
    mindmap_data = generate_mindmap(video_title, summary)

    return jsonify({
        "summary": summary,
        "mindmap": mindmap_data,
        "video_id": video_id,
    })


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=5000)
