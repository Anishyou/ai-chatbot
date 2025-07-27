import weaviate
from app.config import config
from app.logger import get_logger

logger = get_logger("weaviate")

_client = weaviate.Client(config.WEAVIATE_URL)


def get_client() -> weaviate.Client:
    """Returns the connected Weaviate client (singleton)."""
    if not _client.is_ready():
        logger.warning("Weaviate client not ready.")
    return _client


def ensure_webcontent_schema():
    client = get_client()
    class_name = "WebContent"
    schema = client.schema.get()

    if not any(cls["class"] == class_name for cls in schema["classes"]):
        client.schema.create_class({
            "class": class_name,
            "properties": [
                {"name": "text", "dataType": ["text"]},
                {"name": "source", "dataType": ["string"]},
                {"name": "website", "dataType": ["string"]},
            ]
        })
        logger.info("Created schema for WebContent")
    else:
        logger.info("WebContent class already exists")
