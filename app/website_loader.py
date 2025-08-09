import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque
from datetime import datetime, timezone
import trafilatura

from app.logger import get_logger
from app.profile_store import upsert_business_profile
from app.verticals.detect import detect_vertical
from app.verticals.restaurant import extract_restaurant_profile
from app.parsing.contact_hours import (
    extract_jsonld_profiles,
    profile_from_jsonld,
    fallback_contacts,
)

logger = get_logger("loader")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ChatBotCrawler/1.1)"
}

# Street-address pattern (supports multiple languages & formats)
ADDRESS_RE = re.compile(
    r'\b\d{1,5}\s+[A-Z0-9][^\n,]+(?:Street|St\.|Road|Rd\.|Ave|Avenue|Blvd|Way|Lane|Ln\.|Drive|Dr\.|Strasse|Straße|Weg|Platz)\b.*\b\d{4,6}\b',
    re.I
)

# PO Box pattern (common in UAE & Gulf countries)
POBOX_RE = re.compile(
    r'(P\.?O\.?\s*Box\s*\d{3,7}.*?(Dubai|UAE|United Arab Emirates))',
    re.I
)


def _fetch_html(url: str) -> str | None:
    """Fetch raw HTML from a URL with headers and timeout."""
    try:
        resp = requests.get(url, timeout=15, headers=HEADERS)
        if resp.status_code == 200:
            return resp.text
        logger.warning(f"{url} returned status {resp.status_code}")
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
    return None


def is_internal_link(base_url: str, link: str) -> bool:
    """Check if a link belongs to the same domain as the base URL."""
    return urlparse(link).netloc == urlparse(base_url).netloc


def extract_main_text(html: str, url: str) -> str:
    """
    Prefer trafilatura's readability extraction; fall back to headings + paragraphs.
    """
    try:
        out = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            favor_recall=True,
        )
        if out:
            return out
    except Exception:
        pass

    soup = BeautifulSoup(html, "html.parser")
    parts = []
    if soup.title and soup.title.string:
        parts.append(f"Title: {soup.title.string.strip()}")
    for tag in ["h1", "h2", "h3"]:
        for el in soup.find_all(tag):
            t = el.get_text(strip=True)
            if t:
                parts.append(f"{tag.upper()}: {t}")
    for p in soup.find_all("p"):
        para = p.get_text(strip=True)
        if para:
            parts.append(para)
    return "\n".join(parts)


def crawl_website(base_url: str, limit: int = 10) -> list[dict]:
    """
    BFS crawl within the same host. Returns a list of docs:
      { "url", "text", "title", "fetchedAt" }
    """
    visited = set()
    queue = deque([base_url])
    results = []

    while queue and len(results) < limit:
        url = queue.popleft()
        if url in visited:
            continue

        html = _fetch_html(url)
        if not html:
            continue

        try:
            visited.add(url)
            soup = BeautifulSoup(html, "html.parser")
            full_text = extract_main_text(html, url)
            if not full_text.strip():
                logger.info(f"No useful content on {url}")
                continue

            results.append({
                "url": url,
                "text": full_text,
                "title": (soup.title.string.strip() if soup.title and soup.title.string else None),
                "fetchedAt": datetime.now(timezone.utc).isoformat(),
            })

            # enqueue internal links
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("#"):
                    continue
                link = urljoin(url, href)
                link = urldefrag(link)[0].rstrip("/")  # normalize
                if is_internal_link(base_url, link) and link not in visited:
                    queue.append(link)
        except Exception as e:
            logger.warning(f"Failed to crawl {url}: {e}")

    return results


def detect_and_store_site_profile(website: str, docs: list[dict]) -> None:
    """
    Build a structured BusinessProfile for the site and upsert it.

    Strategy:
      - Fetch homepage HTML (JSON-LD & scripts).
      - Detect vertical via heuristics.
      - Extract JSON-LD profile (name, phone, email, address, etc.).
      - Fallback to regex for contact info if missing.
      - Restaurant enrichment (menu parsing).
      - Address fallback from crawled docs (street → PO Box).
    """
    try:
        homepage_html = _fetch_html(website)
        if not homepage_html:
            logger.info("Could not fetch homepage HTML for profile detection.")
            return

        vertical = detect_vertical(homepage_html)

        # JSON-LD profile extraction
        jsonld_profiles = extract_jsonld_profiles(homepage_html)
        base_profile = profile_from_jsonld(jsonld_profiles) if jsonld_profiles else {}

        # Fallback for contact info
        if not base_profile.get("email") or not base_profile.get("telephone"):
            fb = fallback_contacts(homepage_html)
            base_profile.setdefault("email", fb.get("email"))
            base_profile.setdefault("telephone", fb.get("telephone"))

        profile = {
            "website": website,
            "vertical": vertical,
            "name": base_profile.get("name"),
            "telephone": base_profile.get("telephone"),
            "email": base_profile.get("email"),
            "address": base_profile.get("address"),
            "geo": base_profile.get("geo"),
            "openingHours": base_profile.get("openingHours"),
            "priceRange": base_profile.get("priceRange"),
            "social": base_profile.get("sameAs"),
            "menuUrls": [],
            "menuItems": [],
            "cuisines": [],
        }

        # Address fallback: prioritize contact/about pages first
        if not profile.get("address"):
            prio_pages = [d for d in docs if any(x in (d.get("url") or "").lower()
                                                 for x in ("/contact", "/kontakt", "/about", "/impressum", "/contact-us"))]
            other_pages = [d for d in docs if d not in prio_pages]
            for d in prio_pages + other_pages:
                m = ADDRESS_RE.search(d.get("text", "") or "")
                if m:
                    profile["address"] = " ".join(m.group(0).split())  # normalize spaces
                    break

        # If still no address, try PO Box style
        if not profile.get("address"):
            for d in docs:
                m = POBOX_RE.search(d.get("text", "") or "")
                if m:
                    profile["address"] = " ".join(m.group(0).split())
                    break

        # Restaurant-specific enrichment
        if vertical == "restaurant":
            rest = extract_restaurant_profile(website, homepage_html)
            profile["menuUrls"] = rest.get("menuUrls") or []
            profile["menuItems"] = rest.get("menuItems") or []

        upsert_business_profile(profile)
        logger.info("BusinessProfile upserted.")
    except Exception as e:
        logger.warning(f"Profile detection failed: {e}")
