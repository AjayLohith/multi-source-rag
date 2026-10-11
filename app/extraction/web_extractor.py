from typing import Any, Dict
from bs4 import BeautifulSoup
import httpx

from app.extraction.errors import WebExtractionError


def extract_web(url: str, timeout: float = 10.0) -> Dict[str, Any]:
    """
    Fetches and cleans a web page using httpx and BeautifulSoup.
    Strips scripts, styling, navigation, and footers for clean text content.
    """
    try:
        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": "MultiSourceRAG/1.0"},
        )
        response.raise_for_status()
    except Exception as exc:
        raise WebExtractionError(
            message=f"Failed to fetch URL {url}: {exc}",
            source_ref=url,
            error_code="WEB_FETCH_ERROR",
        ) from exc

    try:
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove irrelevant elements
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else url

        # Extract text preserving paragraphs
        paragraphs = [p.get_text().strip() for p in soup.find_all(["p", "h1", "h2", "h3", "h4", "li"])]
        clean_text = "\n\n".join([p for p in paragraphs if p])
        if not clean_text:
            clean_text = soup.get_text(separator="\n", strip=True)

        return {
            "url": str(response.url),
            "title": title,
            "text": clean_text,
            "status_code": response.status_code,
        }
    except Exception as exc:
        raise WebExtractionError(
            message=f"Failed to parse HTML from {url}: {exc}",
            source_ref=url,
            error_code="WEB_PARSE_ERROR",
        ) from exc
