import re
import json
from bs4 import BeautifulSoup


def extract_jsonld_profiles(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    profiles = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                profiles.append(data)
            elif isinstance(data, list):
                profiles.extend(data)
        except Exception:
            continue
    return profiles


def profile_from_jsonld(profiles: list[dict]) -> dict:
    for prof in profiles:
        if "@type" in prof and prof["@type"] in ["Restaurant", "LocalBusiness", "Organization"]:
            return {
                "name": prof.get("name"),
                "telephone": prof.get("telephone"),
                "email": prof.get("email"),
                "address": prof.get("address"),
                "geo": prof.get("geo"),
                "openingHours": prof.get("openingHours"),
                "priceRange": prof.get("priceRange"),
                "sameAs": prof.get("sameAs"),
            }
    return {}


def fallback_contacts(html: str) -> dict:
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html)
    phones = re.findall(r"\+?\d[\d\s().-]{6,}\d", html)
    return {
        "email": emails[0] if emails else None,
        "telephone": phones[0] if phones else None,
    }
