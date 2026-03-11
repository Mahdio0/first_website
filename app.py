"""Flask application for YouTube video summarization and mindmap generation."""

import re

from flask import Flask, jsonify, render_template, request
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from mindmap import generate_mindmap
from summarizer import summarize

app = Flask(__name__)


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
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        formatter = TextFormatter()
        full_text = formatter.format_transcript(transcript)
    except Exception:
        return jsonify({
            "error": "Could not retrieve transcript for this video. "
                     "The video may not have captions available."
        }), 400

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
    app.run(debug=True, port=5000)
