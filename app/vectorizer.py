import uuid
from app.logger import get_logger
from app.weaviate_client import get_client, ensure_webcontent_schema
from app.config import config
from openai import OpenAI

client = OpenAI(api_key=config.OPENAI_API_KEY)
logger = get_logger("vectorizer")

def embed(text: str):
    """Generate vector embedding using OpenAI."""
    response = client.embeddings.create(
        input=text,
        model=config.LLM_EMBEDDING_MODEL
    )
    return response.data[0].embedding

def upload_documents(docs: list, website: str):
    """Upload parsed documents with embeddings into Weaviate."""
    client_weaviate = get_client()
    class_name = "WebContent"

    for doc in docs:
        try:
            vec = embed(doc["text"])
            client_weaviate.data_object.create(
                data_object={
                    "text": doc["text"][:300],  # truncate to avoid overflow
                    "source": doc["url"],
                    "website": website
                },
                class_name=class_name,
                vector=vec,
                uuid=str(uuid.uuid4())
            )
            logger.info(f"Uploaded doc from {doc['url']}")
        except Exception as e:
            logger.error(f"Failed to upload doc from {doc['url']}: {e}")
