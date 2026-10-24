# The AI-Powered News Aggregator & Summarizer

A beginner-friendly Streamlit web app that fetches news from NewsAPI and summarizes individual stories with a local Hugging Face Transformers model. If the model is unavailable, the app falls back to a simple extractive summary.

## Features
- Search news by keywords
- Browse top headlines by category
- English and Hindi language filter
- Sort by date, relevance, or popularity (where supported by the endpoint)
- Filter fetched results by headline/source
- Generate an on-demand summary for each story
- Open the original publisher's article
- Cache API responses for 10 minutes

## Requirements
- Python 3.10 or newer
- A NewsAPI API key: https://newsapi.org/
- Internet connection for news fetching and the first model download

## Setup (Windows)
1. Extract the ZIP file.
2. Open Command Prompt in the project folder.
3. Create a virtual environment:
   ```bash
   py -m venv .venv
   .venv\Scripts\activate
   ```
4. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
5. Copy `.streamlit\secrets.toml.example` to `.streamlit\secrets.toml`.
6. Open `secrets.toml` and replace `YOUR_NEWSAPI_KEY_HERE` with your API key.
7. Start the app:
   ```bash
   streamlit run app.py
   ```
8. Streamlit will open the app in your browser. If it does not, visit the local URL printed in the terminal (usually `http://localhost:8501`).

## Notes
- Keep `secrets.toml` private. Do not upload your API key to GitHub.
- NewsAPI plan limits and endpoint access can affect results.
- The Transformers model is downloaded the first time you summarize a sufficiently long story and can take time/storage. The fallback summarizer does not require the model.
- NewsAPI may return truncated article content; the app summarizes the text supplied by the API, not necessarily the full article.
- For a portfolio/production version, add stronger error handling, source allowlists, tests, deployment secrets, and a dedicated summarization service.
