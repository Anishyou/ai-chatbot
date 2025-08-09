import hashlib
from app.config import config
from app.weaviate_client import get_client
from app.logger import get_logger
from openai import OpenAI

logger = get_logger("vectorizer")
client_oa = OpenAI(api_key=config.OPENAI_API_KEY)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def upload_documents(docs: list[dict], website: str):
    """
    Break docs into chunks and upload to Weaviate.
    """
    if not docs:
        return

    client = get_client()

    for doc in docs:
        text = doc["text"]
        # Simple chunking
        chunks = [text[i : i + 1500] for i in range(0, len(text), 1500)]

        for idx, chunk in enumerate(chunks):
            try:
                emb = client_oa.embeddings.create(
                    input=chunk,
                    model=config.LLM_EMBEDDING_MODEL
                ).data[0].embedding

                client.data_object.create(
                    {
                        "text": chunk,
                        "source": doc["url"],
                        "website": website,
                        "title": doc.get("title"),
                        "section": f"chunk-{idx}",
                        "contentType": "text/html",
                        "fetchedAt": doc.get("fetchedAt"),
                        "hash": _hash_text(chunk),
                    },
                    "WebContent",
                    vector=emb,
                )
            except Exception as e:
                logger.warning(f"Chunk upload failed: {e}")

    logger.info(f"Uploaded {len(docs)} docs for {website}")
