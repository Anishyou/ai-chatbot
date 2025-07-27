from fastapi import FastAPI, Query
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_webcontent_schema()


@app.post("/index")
def index_website(website: str = Query(..., description="Website to index")):
    logger.info(f"Indexing website: {website}")
    docs = crawl_website(website)
    upload_documents(docs, website)
    return {"message": f"Indexed {len(docs)} pages from {website}"}


class AskRequest(BaseModel):
    q: str
    website: str


@app.post("/ask")
def ask_question(req: AskRequest):
    logger.info(f"Query for {req.website}: {req.q}")
    answer = ask(req.q, req.website)
    return {"answer": answer}
