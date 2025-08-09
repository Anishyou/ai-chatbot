from datetime import datetime, timezone
from uuid import uuid5, NAMESPACE_URL
import json

from app.weaviate_client import get_client
from app.logger import get_logger

logger = get_logger("profile_store")

def _as_text(val):
    # Convert lists/dicts to compact JSON string to satisfy "text" properties
    if isinstance(val, (list, dict)):
        return json.dumps(val, separators=(",", ":"))
    return val

def upsert_business_profile(profile: dict):
    """
    Upsert BusinessProfile in Weaviate (one per website).
    Schema expects:
      - openingHours: text (JSON string)
      - menuItems:    text (JSON string)
      - social:       text (JSON string)
      - menuUrls:     text[] (list of strings)
      - cuisines:     string[]
    """
    website = profile["website"]
    obj_id = str(uuid5(NAMESPACE_URL, website))  # stable per-website id

    payload = {
        "website": website,
        "name": profile.get("name"),
        "telephone": profile.get("telephone"),
        "email": profile.get("email"),
        "address": profile.get("address"),
        "geo": profile.get("geo"),
        "openingHours": _as_text(profile.get("openingHours")),  # text
        "menuItems": _as_text(profile.get("menuItems")),        # text
        "social": _as_text(profile.get("social")),              # text
        "menuUrls": profile.get("menuUrls") or [],              # text[]
        "priceRange": profile.get("priceRange"),
        "cuisines": profile.get("cuisines") or [],              # string[]
        "vertical": profile.get("vertical"),
        "lastRefreshed": datetime.now(timezone.utc).isoformat(),
    }

    client = get_client()
    try:
        if client.data_object.exists(obj_id):
            client.data_object.replace(payload, class_name="BusinessProfile", uuid=obj_id)
            logger.info("BusinessProfile replaced.")
        else:
            client.data_object.create(payload, class_name="BusinessProfile", uuid=obj_id)
            logger.info("BusinessProfile created.")
    except Exception as e:
        logger.warning(f"Profile upsert failed: {e}")
