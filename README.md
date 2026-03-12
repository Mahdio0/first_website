# YouTube Video Summarizer & Mindmap

[![CI](https://github.com/Mahdio0/first_website/actions/workflows/ci.yml/badge.svg)](https://github.com/Mahdio0/first_website/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

A web application that takes a YouTube video URL, extracts its transcript, generates a concise summary, and displays an interactive mindmap.

## Features

- **YouTube URL input** – Supports standard, short, and embed URL formats
- **Transcript extraction** – Automatically fetches video captions via `youtube-transcript-api`
- **Extractive summarization** – TF-IDF based sentence scoring (no external API keys required)
- **Interactive mindmap** – Rendered with [markmap](https://markmap.js.org/) for visual exploration of key topics

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Mahdio0/first_website.git
cd first_website

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Then open http://localhost:5000 in your browser.

## Running Tests

```bash
python -m unittest discover tests -v
```

## Render deployment note

When this app is deployed on Render or another shared cloud host, YouTube may block transcript requests from the server IP. The app now returns a clearer deployment-specific error in that case, but the underlying workaround is to retry later or use a proxy/cookies-enabled setup for transcript requests.

## Project Structure

```
├── app.py                  # Flask application and API routes
├── summarizer.py           # Extractive text summarization
├── mindmap.py              # Mindmap data generation
├── requirements.txt        # Python dependencies
├── Procfile                # Process file for PaaS deployment
├── Dockerfile              # Container deployment
├── render.yaml             # Render blueprint for one-click deploy
├── runtime.txt             # Python version specification
├── templates/
│   └── index.html          # Main page template
├── static/
│   ├── css/style.css       # Styling
│   └── js/main.js          # Frontend logic and mindmap rendering
├── tests/
│   └── test_app.py         # Unit tests
└── .github/
    └── workflows/ci.yml    # GitHub Actions CI pipeline
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
