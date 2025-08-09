import json
from typing import List, Dict, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.logger import get_logger
from app.parsing.pdf_image import parse_menu_url
from app.parsing.menu_struct import structure_menu

logger = get_logger("restaurant")

# Heuristics for finding menu links
MENU_HINTS = [
    "menu", "speisekarte", "karte", "essen", "food",
    "drinks", "getränke", "mittags", "mittagsmenü", "wochenkarte"
]
MEDIA_EXTS = (".pdf", ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")


def _discover_menu_urls(base_url: str, soup: BeautifulSoup) -> List[str]:
    urls: List[str] = []
    seen: Set[str] = set()

    # 1) JSON-LD hasMenu (gold when present)
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string)
            items = data if isinstance(data, list) else [data]
            for item in items:
                hm = item.get("hasMenu")
                if isinstance(hm, str):
                    u = urljoin(base_url, hm)
                    if u not in seen:
                        seen.add(u); urls.append(u)
                elif isinstance(hm, list):
                    for v in hm:
                        if isinstance(v, str):
                            u = urljoin(base_url, v)
                            if u not in seen:
                                seen.add(u); urls.append(u)
        except Exception:
            continue

    # 2) Anchors with menu-ish text or file extensions
    for a in soup.find_all("a", href=True):
        text = (a.get_text() or "").lower()
        href = a["href"].lower()
        if any(h in text or h in href for h in MENU_HINTS) or href.endswith(MEDIA_EXTS):
            u = urljoin(base_url, a["href"])
            if u not in seen:
                seen.add(u); urls.append(u)

    return urls


def _scrape_simple_html_menu(url: str) -> str:
    """
    Very light HTML fallback for menu pages that are plain lists/tables.
    Returns plaintext.
    """
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return ""
        page = BeautifulSoup(r.text, "html.parser")

        # Prefer list items and table cells (common on menu pages)
        lines: List[str] = []
        for li in page.find_all("li"):
            t = li.get_text(" ", strip=True)
            if t:
                lines.append(t)
        for td in page.find_all("td"):
            t = td.get_text(" ", strip=True)
            if t:
                lines.append(t)

        # Fallback to all paragraphs if lists/tables are empty
        if not lines:
            for p in page.find_all("p"):
                t = p.get_text(" ", strip=True)
                if t:
                    lines.append(t)

        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Simple HTML scrape failed for {url}: {e}")
        return ""


def extract_restaurant_profile(website: str, homepage_html: str) -> dict:
    """
    Discover menus (HTML/PDF/Image), extract text, and structure into items.
    Returns:
      {
        "menuUrls": [ ... ],
        "menuItems": [ {section, name, price}, ... ]
      }
    """
    soup = BeautifulSoup(homepage_html, "html.parser")

    # Find candidate menu URLs
    menu_urls = _discover_menu_urls(website, soup)
    all_items: List[Dict] = []

    # Parse up to N menu URLs to keep indexing fast/safe
    for u in menu_urls[:6]:
        try:
            # If it's a PDF or image (or unknown), parse via pdf_image helper.
            raw_text = parse_menu_url(u)
            if not raw_text:
                # Try a lightweight HTML scrape as a fallback
                raw_text = _scrape_simple_html_menu(u)

            if not raw_text:
                continue

            items = structure_menu(raw_text)
            if items:
                all_items.extend(items)

        except Exception as e:
            logger.warning(f"Menu parse failed for {u}: {e}")

    # If still nothing, try to pull simple items from homepage itself (rarely enough)
    if not all_items:
        homepage_lines = []
        for li in soup.find_all("li"):
            t = li.get_text(" ", strip=True)
            if t:
                homepage_lines.append(t)
        if homepage_lines:
            items = structure_menu("\n".join(homepage_lines))
            all_items.extend(items)

    # De-duplicate items loosely (name+price)
    dedup_seen = set()
    dedup_items: List[Dict] = []
    for it in all_items:
        key = (it.get("section") or "", (it.get("name") or "").lower(), str(it.get("price") or ""))
        if key in dedup_seen:
            continue
        dedup_seen.add(key)
        dedup_items.append(it)

    return {
        "menuUrls": menu_urls,
        "menuItems": dedup_items[:200],  # cap for payload size
    }
