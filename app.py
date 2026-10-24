import os
from datetime import datetime
import requests
import streamlit as st

st.set_page_config(page_title="AI Newsroom", page_icon="📰", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1200px;}
.news-card {padding: 1rem; border: 1px solid rgba(128,128,128,.25); border-radius: 14px; margin-bottom: 1rem;}
.small-muted {opacity: .72; font-size: .85rem;}
</style>
""", unsafe_allow_html=True)

st.title("📰 The AI-Powered News Aggregator & Summarizer")
st.caption("Find current stories, summarize them, and scan the news faster.")

with st.sidebar:
    st.header("Search the news")
    query = st.text_input("Keywords", value="artificial intelligence")
    category = st.selectbox("Category", [
        "Everything", "Business", "Entertainment", "General", "Health",
        "Science", "Sports", "Technology"
    ])
    language = st.selectbox("Language", ["English", "Hindi"], index=0)
    sort_by = st.selectbox("Sort by", ["Published date", "Relevance", "Popularity"])
    page_size = st.slider("Number of stories", 5, 30, 10, step=5)
    search_clicked = st.button("Fetch news", type="primary", use_container_width=True)
    st.divider()
    st.caption("Add your NewsAPI key in `.streamlit/secrets.toml` or as the `NEWSAPI_KEY` environment variable.")

API_KEY = st.secrets.get("NEWSAPI_KEY", os.getenv("NEWSAPI_KEY", ""))

@st.cache_data(ttl=600, show_spinner=False)
def fetch_news(api_key, q, cat, lang, order, count):
    params = {"apiKey": api_key, "pageSize": count, "language": lang, "sortBy": order}
    if q.strip():
        params["q"] = q.strip()
    if cat != "Everything":
        params["category"] = cat.lower()
    endpoint = "https://newsapi.org/v2/top-headlines" if cat != "Everything" and not q.strip() else "https://newsapi.org/v2/everything"
    if endpoint.endswith("everything"):
        params.pop("category", None)
        params["sortBy"] = "publishedAt" if order == "Published date" else ("popularity" if order == "Popularity" else "relevancy")
    else:
        params.pop("sortBy", None)
        params["country"] = "in"
    response = requests.get(endpoint, params=params, timeout=20)
    data = response.json()
    if response.status_code != 200 or data.get("status") != "ok":
        message = data.get("message", f"NewsAPI returned HTTP {response.status_code}")
        raise RuntimeError(message)
    return data.get("articles", [])

def summarize_text(text, max_sentences=3):
    """Lightweight fallback summarizer; does not require a model download."""
    import re
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return "No article description is available. Open the original source for details."
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(sentences[:max_sentences])

def ai_summarize(text):
    """Use a local Transformers summarization model when enabled; fallback to extractive summary."""
    if not text or not text.strip():
        return "No article description is available. Open the original source for details."
    try:
        from transformers import pipeline
        if "summarizer" not in st.session_state:
            with st.spinner("Loading the AI summarization model (first use may take a while)…"):
                st.session_state.summarizer = pipeline(
                    "summarization", model="sshleifer/distilbart-cnn-12-6"
                )
        cleaned = text.strip()
        if len(cleaned) < 80:
            return summarize_text(cleaned)
        result = st.session_state.summarizer(
            cleaned[:4000], max_length=90, min_length=25, do_sample=False
        )
        return result[0]["summary_text"]
    except Exception:
        return summarize_text(text)

def article_text(article):
    return " ".join(filter(None, [
        article.get("description", ""),
        article.get("content", "")
    ])).strip()

if "articles" not in st.session_state:
    st.session_state.articles = []
if search_clicked:
    st.session_state.articles = []
    if not API_KEY:
        st.error("NewsAPI key not found. Add it to `.streamlit/secrets.toml` or set `NEWSAPI_KEY`.")
    elif not query.strip() and category == "Everything":
        st.warning("Enter a keyword or choose a category.")
    else:
        lang_code = "en" if language == "English" else "hi"
        sort_map = {"Published date": "publishedAt", "Relevance": "relevancy", "Popularity": "popularity"}
        try:
            with st.spinner("Collecting stories…"):
                st.session_state.articles = fetch_news(
                    API_KEY, query, category, lang_code, sort_map[sort_by], page_size
                )
        except Exception as exc:
            st.error(f"Could not fetch news: {exc}")

articles = st.session_state.articles
if not articles and not search_clicked:
    st.info("Choose a topic and click **Fetch news** to load current stories.")
elif not articles and search_clicked and API_KEY:
    st.warning("No stories were returned. Try broader keywords or another category.")

if articles:
    st.subheader(f"Top stories · {len(articles)} results")
    search_filter = st.text_input("Filter these results by headline or source", key="local_filter")
    filtered = [
        a for a in articles
        if search_filter.lower() in (
            (a.get("title") or "") + " " + (a.get("source", {}).get("name") or "")
        ).lower()
    ]
    col1, col2, col3 = st.columns(3)
    col1.metric("Stories loaded", len(articles))
    col2.metric("Sources represented", len({a.get("source", {}).get("name") for a in articles if a.get("source", {}).get("name")}))
    col3.metric("Updated", datetime.now().strftime("%H:%M"))
    for i, article in enumerate(filtered):
        title = article.get("title") or "Untitled story"
        source = (article.get("source") or {}).get("name") or "Unknown source"
        published = article.get("publishedAt", "")
        description = article.get("description") or ""
        url = article.get("url") or ""
        with st.container(border=True):
            st.markdown(f"### {title}")
            st.markdown(f"<div class='small-muted'>{source} · {published}</div>", unsafe_allow_html=True)
            if description:
                st.write(description)
            left, right = st.columns([1, 5])
            with left:
                if st.button("✨ Summarize", key=f"summarize_{i}"):
                    summary = ai_summarize(article_text(article) or description or title)
                    st.session_state[f"summary_{i}"] = summary
            with right:
                if url:
                    st.link_button("Read original article ↗", url)
            if st.session_state.get(f"summary_{i}"):
                st.markdown("**Summary**")
                st.write(st.session_state[f"summary_{i}"])
                st.caption("Summaries are AI-generated or extractive fallbacks. Verify important details against the original article.")

st.divider()
st.caption("News content is provided by NewsAPI and its publishers. This demo displays headlines and descriptions, not full copyrighted articles.")
