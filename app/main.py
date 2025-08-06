from fastapi import FastAPI, Query, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.chatbot import ask
from app.config import config
from app.logger import get_logger
from app.vectorizer import upload_documents
from app.weaviate_client import get_client, ensure_webcontent_schema
from app.website_loader import crawl_website

app = FastAPI()
logger = get_logger("main")

# Enable CORS based on allowed origins in config
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure schema exists in Weaviate
ensure_webcontent_schema()

# ----------------------------
# Utility: check if website is indexed in Weaviate
# ----------------------------
def is_website_indexed(website: str) -> bool:
    client = get_client()
    try:
        result = client.query.get(
            "WebContent",
            ["_additional { id }"]
        ).with_where({
            "path": ["website"],  # ✅ correct field
            "operator": "Equal",
            "valueText": website
        }).with_limit(1).do()

        docs = result.get("data", {}).get("Get", {}).get("WebContent", [])
        return len(docs) > 0
    except Exception as e:
        logger.error(f"Failed to check if website is indexed: {e}")
        return False



# ----------------------------
# Admin-only indexing endpoint
# ----------------------------
@app.post("/index")
def index_website(
        website: str = Query(..., description="Website to index"),
        x_index_token: str = Header(..., alias="X-INDEX-TOKEN")
):
    if x_index_token != config.INDEX_SECRET:
        logger.warning(f"Unauthorized index attempt for {website}")
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.info(f"Indexing website: {website}")
    docs = crawl_website(website)
    upload_documents(docs, website)

    return {"message": f"Indexed {len(docs)} pages from {website}"}


# ----------------------------
# Ask API — only for indexed websites
# ----------------------------
class AskRequest(BaseModel):
    q: str
    website: str


@app.post("/ask")
def ask_question(req: AskRequest):
    if not is_website_indexed(req.website):
        logger.warning(f"Blocked query for unindexed website: {req.website}")
        raise HTTPException(status_code=403, detail="Website not indexed")

    logger.info(f"Query for {req.website}: {req.q}")
    answer = ask(req.q, req.website)
    return {"answer": answer}

@app.get("/health")
def health_check():
    return {"status": "ok"}
