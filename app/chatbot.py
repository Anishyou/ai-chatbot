import json
from openai import OpenAI
from app.config import config
from app.logger import get_logger
from app.weaviate_client import get_client

logger = get_logger("chatbot")
client_oa = OpenAI(api_key=config.OPENAI_API_KEY)


def _fetch_profile_facts(website: str) -> dict:
    """
    Fetch stored BusinessProfile facts from Weaviate.
    """
    client = get_client()
    try:
        result = client.query.get(
            "BusinessProfile",
            [
                "name", "telephone", "email", "address",
                "openingHours", "menuUrls", "menuItems",
                "priceRange", "cuisines", "social", "vertical"
            ]
        ).with_where({
            "path": ["website"],
            "operator": "Equal",
            "valueText": website
        }).with_limit(1).do()

        items = result.get("data", {}).get("Get", {}).get("BusinessProfile", [])
        return items[0] if items else {}
    except Exception as e:
        logger.warning(f"Profile fetch failed: {e}")
        return {}


def ask(question: str, website: str) -> str:
    profile = _fetch_profile_facts(website)

    # If Q matches a fact directly
    q_lower = question.lower()
    if "phone" in q_lower or "call" in q_lower:
        if profile.get("telephone"):
            return f"The phone number is {profile['telephone']}"
    if "email" in q_lower:
        if profile.get("email"):
            return f"The email address is {profile['email']}"
    if "address" in q_lower or "where" in q_lower:
        if profile.get("address"):
            return f"The address is {profile['address']}"
    if "menu" in q_lower:
        if profile.get("menuUrls"):
            return f"Menu: {', '.join(profile['menuUrls'])}"

    # Otherwise do vector search
    client = get_client()
    try:
        emb = client_oa.embeddings.create(
            input=question,
            model=config.LLM_EMBEDDING_MODEL
        ).data[0].embedding

        res = client.query.get(
            "WebContent",
            ["text", "source", "title"]
        ).with_near_vector({"vector": emb, "certainty": 0.7}) \
            .with_where({"path": ["website"], "operator": "Equal", "valueText": website}) \
            .with_limit(4).do()

        docs = res.get("data", {}).get("Get", {}).get("WebContent", [])
        context = "\n\n".join(f"{d.get('title') or ''}\n{d['text']}" for d in docs)

        prompt = f"Answer the question based on the context below.\n\nContext:\n{context}\n\nQ: {question}\nA:"
        resp = client_oa.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Vector Q failed: {e}")
        return "Sorry, I couldn't find an answer."
