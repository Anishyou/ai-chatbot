# Website Chatbot (FastAPI + Weaviate)

A production-ready Python service for a domain-restricted website chatbot powered by **FastAPI** and **Weaviate**.  
It crawls and indexes website content into a vector database, and answers questions **only** using the ingested content.

---

## ✨ Features

- 🚀 **FastAPI** backend with OpenAPI docs
- 📚 Retrieval-Augmented Generation (RAG) using **Weaviate**
- 🤖 OpenAI embeddings & responses
- 🐳 Docker & Docker Compose ready
- 🔒 Domain-restricted answering
- 📦 Configurable via `.env`

---

## 📂 Project Structure

```
chatbot/
├── app/
│   ├── parsing/
│   │   ├── contact_hours.py
│   │   ├── menu_struct.py
│   │   └── pdf_image.py
│   ├── verticals/
│   │   ├── detect.py
│   │   ├── restaurant.py
│   │   └── __init__.py
│   ├── chatbot.py
│   ├── config.py
│   ├── logger.py
│   ├── main.py
│   ├── profile_store.py
│   ├── vectorizer.py
│   ├── weaviate_client.py
│   └── website_loader.py
├── config/
├── .dockerignore
├── .env
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── poetry.lock
└── README.md
```

---

## ⚙️ Setup

### 1) Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional but recommended)
- `TOKEN` and `OPENAI_API_KEY` in `.env`
- A running Weaviate instance

### 2) Environment Variables

| Variable | Description |
|---|---|
| TOKEN | Authentication token for accessing the API |
| OPENAI_API_KEY | API key for OpenAI (used for embeddings/generation) |
| WEAVIATE_URL | Base URL of your Weaviate instance |
| WEAVIATE_API_KEY | API key for Weaviate (if required) |
| ALLOWED_DOMAIN | Domain the chatbot is allowed to answer from |


Create your `.env` file:

```bash
cp .env.example .env
# then edit .env with your keys and URLs
#Add OPENAI_API_KEY-""
# Add INDEX_SECRET-""


```

### 3) Install dependencies (local dev)

```bash
pip install -r requirements.txt
# or if using Poetry:
poetry install
```

---

## 🚀 Running the Service

### Local (dev)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t chatbot-app .
docker run --env-file .env -p 8000:8000 chatbot-app
```

### Docker Compose

```bash
docker compose up --build
```

---

## 🔌 API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | /ingest | Crawl/ingest pages for the configured domain(s) |
| POST | /ask | Ask a question and get an answer grounded in ingested data |
| GET | /health | Service health check |
| GET | /docs | OpenAPI/Swagger UI |

Once running, open: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 🛠 Development Notes

- Code style: `black` + `isort` + `flake8`
- Tests: `pytest -q`
- Logging: structured JSON logging is recommended

---

## 🐳 Docker Compose Services

| Service | Description |
|---|---|
| chatbot-app | FastAPI backend |
| weaviate    | Vector database for embeddings & retrieval |

---

## 📜 License

MIT License — feel free to use and adapt.

---

## 🤝 Contributing

1. Fork the repo
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Create a Pull Request
