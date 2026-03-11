# YouTube Video Summarizer & Mindmap

A web application that takes a YouTube video URL, extracts its transcript, generates a concise summary, and displays an interactive mindmap.

## Features

- **YouTube URL input** – Supports standard, short, and embed URL formats
- **Transcript extraction** – Automatically fetches video captions via `youtube-transcript-api`
- **Extractive summarization** – TF-IDF based sentence scoring (no external API keys required)
- **Interactive mindmap** – Rendered with [markmap](https://markmap.js.org/) for visual exploration of key topics

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Then open http://localhost:5000 in your browser.

## Running Tests

```bash
python -m unittest tests.test_app -v
```

## Project Structure

```
├── app.py              # Flask application and API routes
├── summarizer.py       # Extractive text summarization
├── mindmap.py          # Mindmap data generation
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Main page template
├── static/
│   ├── css/style.css   # Styling
│   └── js/main.js      # Frontend logic and mindmap rendering
└── tests/
    └── test_app.py     # Unit tests
```