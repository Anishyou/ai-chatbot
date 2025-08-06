import uuid
import textwrap
from app.logger import get_logger
from app.weaviate_client import get_client, ensure_webcontent_schema
from app.config import config
from openai import OpenAI

logger = get_logger("vectorizer")
client = OpenAI(api_key=config.OPENAI_API_KEY)

# Constants
CHUNK_SIZE = 500  # characters, adjust as needed

def embed(text: str):
    """Generate vector embedding using OpenAI."""
    response = client.embeddings.create(
        input=text,
        model=config.LLM_EMBEDDING_MODEL
    )
    return response.data[0].embedding


def split_text(text: str, max_chars: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks to improve embedding granularity."""
    if not text:
        return []
    return textwrap.wrap(text, width=max_chars, break_long_words=False, break_on_hyphens=False)


def upload_documents(docs: list, website: str):
    """Upload parsed documents with embeddings into Weaviate."""
    client_weaviate = get_client()
    class_name = "WebContent"

    for doc in docs:
        try:
            chunks = split_text(doc.get("text", ""), max_chars=CHUNK_SIZE)
            if not chunks:
                logger.warning(f"No text found in document: {doc.get('url')}")
                continue

            for chunk in chunks:
                vec = embed(chunk)
                client_weaviate.data_object.create(
                    data_object={
                        "text": chunk,
                        "source": doc.get("url"),
                        "website": website
                    },
                    class_name=class_name,
                    vector=vec,
                    uuid=str(uuid.uuid4())
                )
                logger.info(f"Uploaded chunk from {doc.get('url')}")

        except Exception as e:
            logger.error(f"Failed to upload doc from {doc.get('url')}: {e}")
