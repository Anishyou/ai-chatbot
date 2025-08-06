import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from app.logger import get_logger

logger = get_logger("loader")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ChatBotCrawler/1.0)"
}


def is_internal_link(base_url, link):
    return urlparse(link).netloc == urlparse(base_url).netloc


def extract_metadata(soup: BeautifulSoup):
    meta_data = []
    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("property")
        content = tag.get("content")
        if name and content:
            meta_data.append(f"{name}: {content}")
    return meta_data


def extract_image_alts(soup: BeautifulSoup):
    return [img.get("alt", "") for img in soup.find_all("img") if img.get("alt")]


def extract_text_from_page(soup: BeautifulSoup):
    parts = []

    # Page title
    if soup.title and soup.title.string:
        parts.append(f"Title: {soup.title.string.strip()}")

    # Headings
    for tag in ["h1", "h2", "h3"]:
        for el in soup.find_all(tag):
            heading = el.get_text(strip=True)
            if heading:
                parts.append(f"{tag.upper()}: {heading}")

    # Paragraphs
    for p in soup.find_all("p"):
        para = p.get_text(strip=True)
        if para:
            parts.append(para)

    # Image alt texts
    parts.extend(extract_image_alts(soup))

    # Metadata
    parts.extend(extract_metadata(soup))

    return "\n".join(parts)


def crawl_website(base_url: str, limit: int = 10):
    visited = set()
    queue = deque([base_url])
    results = []

    while queue and len(results) < limit:
        url = queue.popleft()
        if url in visited:
            continue

        try:
            visited.add(url)
            resp = requests.get(url, timeout=10, headers=HEADERS)
            if resp.status_code != 200:
                logger.warning(f"{url} returned status {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            full_text = extract_text_from_page(soup)
            if not full_text.strip():
                logger.info(f"No useful content on {url}")
                continue

            results.append({"url": url, "text": full_text})
            logger.info(f"Crawled: {url} (chars: {len(full_text)})")

            # Add internal links
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])
                if is_internal_link(base_url, link) and link not in visited:
                    queue.append(link)

        except Exception as e:
            logger.warning(f"Failed to crawl {url}: {e}")

    return results
