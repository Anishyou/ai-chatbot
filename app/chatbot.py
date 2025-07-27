from app.logger import get_logger
from app.weaviate_client import get_client as get_weaviate_client
from app.config import config
from app.website_loader import crawl_website
from app.vectorizer import upload_documents
from openai import OpenAI

logger = get_logger("chatbot")

# Initialize OpenAI client once
client_openai = OpenAI(api_key=config.OPENAI_API_KEY)


def ask(query: str, website: str) -> str:
    # 1. Embed the query
    embedding_response = client_openai.embeddings.create(
        input=query,
        model=config.LLM_EMBEDDING_MODEL
    )
    query_vector = embedding_response.data[0].embedding

    # 2. Query Weaviate
    client_weaviate = get_weaviate_client()
    try:
        result = (
            client_weaviate.query
            .get("WebContent", ["text", "source"])
            .with_near_vector({"vector": query_vector})
            .with_where({
                "path": ["website"],
                "operator": "Equal",
                "valueString": website
            })
            .with_limit(3)
            .do()
        )

        docs = result["data"]["Get"].get("WebContent", [])
        context = " ".join(doc["text"] for doc in docs)

    except Exception as e:
        logger.warning(f"Vector DB query failed: {e}")
        context = ""

    # 3. Fallback: Live crawl if context is empty
    if not context.strip():
        logger.info(f"No vector results found for {website}, crawling live...")
        docs = crawl_website(website, limit=5)
        upload_documents(docs, website)
        context = " ".join(doc["text"] for doc in docs if "text" in doc)

    # 4. Compose GPT messages
    messages = [
        {
            "role": "system",
            "content": (
                f"You are an assistant for {website}. "
                "Use the provided context if available. "
                "If the context is missing or insufficient, use general knowledge."
            )
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {query}"
        }
    ]

    # 5. Ask OpenAI GPT model
    response = client_openai.chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages
    )

    return response.choices[0].message.content
