import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.tools import tool
from tavily import TavilyClient

load_dotenv()

_api_key = os.getenv("TAVILY_API_KEY")
if not _api_key:
    raise RuntimeError(
        "TAVILY_API_KEY is not set. Add it to your .env file next to GROQ_API_KEY."
    )

tavily = TavilyClient(api_key=_api_key)

# Tool output is fed back into the model on every subsequent turn, and Groq's free
# tier allows only 8000 tokens per minute, so keep it small.
MAX_RESULTS = 5
SNIPPET_CHARS = 300
SCRAPE_CHARS = 3000


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic . Returns Titles , URLs and snippets."""
    try:
        results = tavily.search(query=query, max_results=MAX_RESULTS)
    except Exception as e:
        return f"Search failed: {e}"

    hits = results.get("results", []) if isinstance(results, dict) else []
    if not hits:
        return f"No search results found for: {query}"

    out = []
    for r in hits:
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        content = (r.get("content") or "")[:SNIPPET_CHARS]
        out.append(f"Title: {title}\nURL: {url}\nSnippet: {content}\n")

    return "\n----\n".join(out)


@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        # Without this, a 404/403 error page gets scraped and returned as if it
        # were real article content.
        resp.raise_for_status()

        ctype = resp.headers.get("Content-Type", "")
        if "html" not in ctype and "text" not in ctype:
            return f"Could not scrape URL: unsupported content type '{ctype}'"

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)[:SCRAPE_CHARS]
        if not text.strip():
            return f"Could not scrape URL: no readable text found at {url}"
        return text
    except Exception as e:
        return f"Could not scrape URL: {str(e)}"
