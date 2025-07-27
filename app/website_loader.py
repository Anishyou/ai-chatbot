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
            text = soup.get_text(separator=" ", strip=True)
            results.append({"url": url, "text": text})
            logger.info(f"Crawled: {url} (chars: {len(text)})")

            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])
                if is_internal_link(base_url, link) and link not in visited:
                    queue.append(link)

        except Exception as e:
            logger.warning(f"Failed to crawl {url}: {e}")

    return results
