from fastapi import FastAPI, Query, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from openai import OpenAI

from app.chatbot import ask
from app.config import config
from app.logger import get_logger
from app.vectorizer import upload_documents
from app.weaviate_client import get_client, ensure_webcontent_schema
from app.website_loader import crawl_website, detect_and_store_site_profile

app = FastAPI()
logger = get_logger("main")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure schema exists in Weaviate
ensure_webcontent_schema()


def is_website_indexed(website: str) -> bool:
    """Check if site is already in Weaviate."""
    client = get_client()
    try:
        result = (
            client.query.get("WebContent", ["_additional { id }"])
            .with_where({
                "path": ["website"],
                "operator": "Equal",
                "valueText": website
            })
            .with_limit(1)
            .do()
        )
        docs = result.get("data", {}).get("Get", {}).get("WebContent", [])
        return len(docs) > 0
    except Exception as e:
        logger.error(f"Check index failed: {e}")
        return False


@app.post("/index")
def index_website(
        website: str = Query(..., description="Website to index"),
        x_index_token: str = Header(..., alias="X-INDEX-TOKEN")
):
    """Admin-only: Crawl & index site content + detect profile."""
    if x_index_token != config.INDEX_SECRET:
        logger.warning(f"Unauthorized index attempt for {website}")
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.info(f"Indexing website: {website}")
    docs = crawl_website(website)
    upload_documents(docs, website)

    # Detect menus, contact info, business type
    detect_and_store_site_profile(website, docs)

    return {"message": f"Indexed {len(docs)} pages from {website}"}

class TeachRequest(BaseModel):
    website: str
    question: str
    answer: str
    token: str

@app.post("/teach")
def teach_custom_qa(req: TeachRequest):
    if req.token != config.INDEX_SECRET:
        raise HTTPException(status_code=403, detail="Invalid token")

    weaviate_client = get_client()
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

    try:
        emb_response = openai_client.embeddings.create(
            model=config.LLM_EMBEDDING_MODEL,   # <-- FIXED
            input=req.question
        )
        vector = emb_response.data[0].embedding
    except Exception as e:
        # better error visibility
        raise HTTPException(status_code=500, detail=f"Embedding creation failed: {repr(e)}")

    obj = {
        "website": req.website,
        "question": req.question,
        "answer": req.answer,
        "createdAt": datetime.now(timezone.utc).isoformat()
    }

    try:
        weaviate_client.data_object.create(
            data_object=obj,
            class_name="CustomQA",
            vector=vector
        )
        return {"status": "success", "message": "Custom QA added with embedding"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store QA: {repr(e)}")



class AskRequest(BaseModel):
    q: str
    website: str

@app.post("/ask")
def ask_endpoint(req: AskRequest):
    client = get_client()
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

    emb_response = openai_client.embeddings.create(
        model=config.LLM_EMBEDDING_MODEL,      # <-- FIXED
        input=req.q
    )
    query_vector = emb_response.data[0].embedding

    wc_results = client.query.get(
        "WebContent", ["text", "source"]
    ).with_near_vector({"vector": query_vector}).with_where({
        "path": ["website"], "operator": "Equal", "valueText": req.website
    }).with_limit(3).do().get("data", {}).get("Get", {}).get("WebContent", [])

    qa_results = client.query.get(
        "CustomQA", ["question", "answer"]
    ).with_near_vector({"vector": query_vector}).with_where({
        "path": ["website"], "operator": "Equal", "valueText": req.website
    }).with_limit(3).do().get("data", {}).get("Get", {}).get("CustomQA", [])

    context_parts = [r.get("text","") for r in wc_results] + [
        f"Q: {r.get('question')}\nA: {r.get('answer')}" for r in qa_results
    ]
    context = "\n\n".join(context_parts)

    completion = openai_client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": "Answer based only on the provided context."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {req.q}"}
        ]
        # don't set temperature if your model doesn't support it
    )
    return completion.choices[0].message.content.strip()

@app.get("/health")
def health_check():
    return {"status": "ok"}
