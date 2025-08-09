import weaviate
from app.config import config
from app.logger import get_logger

logger = get_logger("weaviate")

_client = None


def get_client() -> weaviate.Client:
    """Lazy-init Weaviate client and return it."""
    global _client
    if _client is None:
        _client = weaviate.Client(config.WEAVIATE_URL)
    try:
        if not _client.is_ready():
            logger.warning("Weaviate client not ready (is_ready() returned False).")
    except Exception as e:
        logger.warning(f"Weaviate readiness check failed: {e}")
    return _client

def ensure_webcontent_schema():
    """
    Ensure all required classes exist in Weaviate:
    - WebContent: embedded text chunks
    - BusinessProfile: structured per-website facts
    - CustomQA: manually fed Q&A pairs
    """
    client = get_client()
    try:
        schema = client.schema.get()
    except Exception as e:
        logger.error(f"Failed to get Weaviate schema: {e}")
        return

    existing = {cls.get("class") for cls in schema.get("classes", [])}

    # --- WebContent: embedded text chunks ---
    if "WebContent" not in existing:
        try:
            client.schema.create_class({
                "class": "WebContent",
                "vectorIndexConfig": {"distance": "cosine"},
                "properties": [
                    {"name": "text", "dataType": ["text"]},
                    {"name": "source", "dataType": ["string"]},
                    {"name": "website", "dataType": ["string"]},
                    {"name": "title", "dataType": ["string"]},
                    {"name": "section", "dataType": ["string"]},
                    {"name": "contentType", "dataType": ["string"]},
                    {"name": "fetchedAt", "dataType": ["date"]},
                    {"name": "hash", "dataType": ["string"]},
                ],
            })
            logger.info("Created schema for WebContent")
        except Exception as e:
            logger.error(f"Creating WebContent class failed: {e}")
    else:
        logger.info("WebContent class exists")

    # --- BusinessProfile: structured per-website facts ---
    if "BusinessProfile" not in existing:
        try:
            client.schema.create_class({
                "class": "BusinessProfile",
                "properties": [
                    {"name": "website", "dataType": ["string"]},
                    {"name": "name", "dataType": ["string"]},
                    {"name": "telephone", "dataType": ["string"]},
                    {"name": "email", "dataType": ["string"]},
                    {"name": "address", "dataType": ["text"]},
                    {"name": "geo", "dataType": ["string"]},
                    {"name": "openingHours", "dataType": ["text"]},  # JSON string
                    {"name": "menuUrls", "dataType": ["text[]"]},
                    {"name": "menuItems", "dataType": ["text"]},     # JSON string
                    {"name": "priceRange", "dataType": ["string"]},
                    {"name": "cuisines", "dataType": ["string[]"]},
                    {"name": "social", "dataType": ["text"]},        # JSON string or CSV
                    {"name": "vertical", "dataType": ["string"]},
                    {"name": "lastRefreshed", "dataType": ["date"]},
                ],
            })
            logger.info("Created schema for BusinessProfile")
        except Exception as e:
            logger.error(f"Creating BusinessProfile class failed: {e}")
    else:
        logger.info("BusinessProfile class exists")

    # --- CustomQA: manually fed Q&A pairs ---
    if "CustomQA" not in existing:
        try:
            client.schema.create_class({
                "class": "CustomQA",
                "vectorIndexConfig": {"distance": "cosine"},
                "properties": [
                    {"name": "website", "dataType": ["string"]},
                    {"name": "question", "dataType": ["text"]},
                    {"name": "answer", "dataType": ["text"]},
                    {"name": "createdAt", "dataType": ["date"]},
                ],
            })
            logger.info("Created schema for CustomQA")
        except Exception as e:
            logger.error(f"Creating CustomQA class failed: {e}")
    else:
        logger.info("CustomQA class exists")
