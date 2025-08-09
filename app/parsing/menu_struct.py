"""
Turn raw menu text into structured items.
Handles simple 'Name ... €12.90' patterns and section headers.
"""

import re
from typing import List, Dict

PRICE_RE = re.compile(
    r"(?P<price>\d{1,3}(?:[.,]\d{1,2})?)\s?(?:€|eur|euro)?",
    re.IGNORECASE,
)

SECTION_HINT_RE = re.compile(
    r"^(vorspeisen|hauptgerichte|dessert|nachspeisen|beilagen|getränke|drinks|starters|mains|main courses|desserts|sides|lunch|wochenkarte|mittag|pizza|pasta|salads?)[:\s-]*$",
    re.IGNORECASE,
)

SEPARATOR_RE = re.compile(r"\s{2,}|[-–·•]\s|:\s")


def _looks_like_section(line: str) -> bool:
    """Heuristic: matches known section keywords."""
    return bool(SECTION_HINT_RE.match(line.strip()))


def structure_menu(text: str) -> List[Dict]:
    """
    Given raw menu text, return a list of items:
    [{section, name, price}, ...]
    """
    items = []
    current_section = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Detect section header
        if _looks_like_section(line):
            current_section = line
            continue

        # Try to split into name + price
        price_match = PRICE_RE.search(line)
        if price_match:
            price = price_match.group("price")
            # Remove price from name
            name = PRICE_RE.sub("", line).strip(" -–·•")
            items.append({
                "section": current_section,
                "name": name,
                "price": price,
            })
        else:
            # No price: treat as standalone item
            items.append({
                "section": current_section,
                "name": line,
                "price": None,
            })

    return items
