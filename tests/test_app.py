"""Tests for the summarizer, mindmap generator, and Flask API."""

import json
import unittest
from unittest.mock import MagicMock, patch

from app import app, extract_video_id
from mindmap import generate_mindmap
from summarizer import summarize


class TestExtractVideoId(unittest.TestCase):
    """Tests for YouTube video ID extraction."""

    def test_standard_url(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_short_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_embed_url(self):
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_bare_id(self):
        self.assertEqual(extract_video_id("dQw4w9WgXcQ"), "dQw4w9WgXcQ")

    def test_invalid_url(self):
        self.assertIsNone(extract_video_id("not-a-youtube-url"))

    def test_empty_string(self):
        self.assertIsNone(extract_video_id(""))

    def test_url_with_extra_params(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")


class TestSummarizer(unittest.TestCase):
    """Tests for the text summarizer."""

    def test_empty_text(self):
        self.assertEqual(summarize(""), "")
        self.assertEqual(summarize("   "), "")

    def test_short_text_returned_as_is(self):
        text = "This is a short sentence. It has only two sentences."
        result = summarize(text, num_sentences=5)
        self.assertEqual(result, text)

    def test_summarize_reduces_length(self):
        sentences = [f"Sentence number {i} about topic {i % 3}." for i in range(20)]
        text = " ".join(sentences)
        result = summarize(text, num_sentences=5)
        result_sentences = [s.strip() for s in result.split(".") if s.strip()]
        self.assertLessEqual(len(result_sentences), 6)  # allow slight variance
        self.assertGreater(len(result), 0)

    def test_summarize_preserves_order(self):
        sentences = [f"Sentence {i} about unique topic {chr(65 + i)}." for i in range(10)]
        text = " ".join(sentences)
        result = summarize(text, num_sentences=3)
        # Verify result sentences appear in original order
        indices = []
        for sent in result.split("."):
            sent = sent.strip()
            if sent:
                for i, orig in enumerate(sentences):
                    if sent in orig:
                        indices.append(i)
                        break
        self.assertEqual(indices, sorted(indices))


class TestMindmapGenerator(unittest.TestCase):
    """Tests for mindmap generation."""

    def test_empty_summary(self):
        result = generate_mindmap("Test Video", "")
        self.assertEqual(result["name"], "Test Video")
        self.assertEqual(result["children"], [])

    def test_basic_structure(self):
        summary = (
            "Python is a programming language. It is widely used for web development. "
            "Machine learning relies on Python libraries. Data science uses Python tools. "
            "Flask is a Python web framework. Django is another Python framework."
        )
        result = generate_mindmap("Python Overview", summary)
        self.assertEqual(result["name"], "Python Overview")
        self.assertIsInstance(result["children"], list)
        self.assertGreater(len(result["children"]), 0)

        for child in result["children"]:
            self.assertIn("name", child)
            self.assertIn("children", child)

    def test_single_sentence_summary(self):
        result = generate_mindmap("Title", "Just one single sentence here.")
        self.assertEqual(result["name"], "Title")
        self.assertGreaterEqual(len(result["children"]), 1)


class TestFlaskAPI(unittest.TestCase):
    """Tests for the Flask API endpoints."""

    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    def test_index_page(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"YouTube Video Summarizer", resp.data)

    def test_api_missing_url(self):
        resp = self.client.post(
            "/api/summarize",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("error", data)

    def test_api_empty_url(self):
        resp = self.client.post(
            "/api/summarize",
            data=json.dumps({"url": ""}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_api_invalid_url(self):
        resp = self.client.post(
            "/api/summarize",
            data=json.dumps({"url": "not-a-valid-url"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("Invalid YouTube URL", data["error"])

    @patch("app.YouTubeTranscriptApi")
    def test_api_success(self, mock_ytt_class):
        mock_api = MagicMock()
        mock_ytt_class.return_value = mock_api

        mock_snippet = MagicMock()
        mock_snippet.text = "Hello world"

        mock_api.fetch.return_value = [mock_snippet]

        with patch("app.TextFormatter") as mock_fmt_class:
            mock_formatter = MagicMock()
            mock_fmt_class.return_value = mock_formatter
            mock_formatter.format_transcript.return_value = (
                "Python is a great programming language. "
                "It is used in web development and data science. "
                "Machine learning is a popular field. "
                "Flask is a lightweight web framework."
            )

            resp = self.client.post(
                "/api/summarize",
                data=json.dumps({"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}),
                content_type="application/json",
            )
            self.assertEqual(resp.status_code, 200)
            data = json.loads(resp.data)
            self.assertIn("summary", data)
            self.assertIn("mindmap", data)
            self.assertIn("video_id", data)
            self.assertEqual(data["video_id"], "dQw4w9WgXcQ")

    @patch("app.YouTubeTranscriptApi")
    def test_api_transcript_error(self, mock_ytt_class):
        mock_api = MagicMock()
        mock_ytt_class.return_value = mock_api
        mock_api.fetch.side_effect = Exception("No transcript")
        mock_api.list.side_effect = Exception("No transcripts available")

        resp = self.client.post(
            "/api/summarize",
            data=json.dumps({"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("Could not retrieve transcript", data["error"])

    @patch("app.YouTubeTranscriptApi")
    def test_api_fallback_to_non_english_transcript(self, mock_ytt_class):
        mock_api = MagicMock()
        mock_ytt_class.return_value = mock_api
        mock_api.fetch.side_effect = Exception("No English transcript")

        # Simulate a non-English transcript available via list()
        mock_transcript_obj = MagicMock()
        mock_transcript_obj.language_code = "fr"
        mock_translated = MagicMock()
        mock_transcript_obj.translate.return_value = mock_translated

        mock_snippet = MagicMock()
        mock_snippet.text = "Bonjour le monde"
        mock_translated.fetch.return_value = [mock_snippet]

        mock_api.list.return_value = iter([mock_transcript_obj])

        with patch("app.TextFormatter") as mock_fmt_class:
            mock_formatter = MagicMock()
            mock_fmt_class.return_value = mock_formatter
            mock_formatter.format_transcript.return_value = (
                "Python is a great programming language. "
                "It is used in web development and data science. "
                "Machine learning is a popular field. "
                "Flask is a lightweight web framework."
            )

            resp = self.client.post(
                "/api/summarize",
                data=json.dumps({"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}),
                content_type="application/json",
            )
            self.assertEqual(resp.status_code, 200)
            data = json.loads(resp.data)
            self.assertIn("summary", data)
            self.assertIn("mindmap", data)
            mock_transcript_obj.translate.assert_called_once_with("en")

    @patch("app.YouTubeTranscriptApi")
    def test_api_fallback_no_transcripts_available(self, mock_ytt_class):
        mock_api = MagicMock()
        mock_ytt_class.return_value = mock_api
        mock_api.fetch.side_effect = Exception("No English transcript")
        mock_api.list.return_value = iter([])

        resp = self.client.post(
            "/api/summarize",
            data=json.dumps({"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("Could not retrieve transcript", data["error"])


if __name__ == "__main__":
    unittest.main()
