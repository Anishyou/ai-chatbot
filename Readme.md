# 🤖 FastAPI + Weaviate Chatbot

A production-ready chatbot backend using FastAPI, OpenAI, and Weaviate vector database. It allows secure website indexing and question answering only for indexed sites.

---

## 🚀 Features

- 🔒 Secure indexing via API token (`X-INDEX-TOKEN`)
- 📄 Live crawling + chunked document embedding
- 🔍 Retrieval-augmented generation (RAG) using GPT
- 🧠 Vector storage via Weaviate
- ✅ CORS and health checks
- 📦 Docker + Docker Compose support

---

## 🛠️ Project Structure

```
├── app/
│   ├── main.py                # FastAPI entry point
│   ├── chatbot.py             # LLM interaction logic
│   ├── config.py              # Loads YAML + .env configs
│   ├── logger.py              # Logger setup
│   ├── website_loader.py      # Crawler for websites
│   ├── vectorizer.py          # Embedding + Weaviate upload
│   └── weaviate_client.py     # Client + schema creation
├── config/
│   ├── application.yml        # App and Weaviate config
│   └── llm_config.yml         # OpenAI models
├── .env                       # API secrets
├── Dockerfile                 # Python + Uvicorn
├── docker-compose.yml         # Local multi-service setup
└── requirements.txt           # Python dependencies
```

---

## 🧪 Local Development

### 1. Clone + Configure
```bash
git clone https://github.com/yourname/chatbot.git
cd chatbot
cp .env.example .env  # or create one manually
```

### 2. Edit `.env`
```env
OPENAI_API_KEY=your-openai-key
INDEX_SECRET=some-secret-token
```

### 3. Run Docker
```bash
docker compose up --build
```

> - FastAPI: [http://localhost:8000/docs](http://localhost:8000/docs)
> - Weaviate: [http://localhost:8080/v1/.well-known/ready](http://localhost:8080/v1/.well-known/ready)

---

## ⚙️ Configuration

### `config/application.yml`
```yaml
app:
  port: 8000
  host: "0.0.0.0"
  allowed_origins:
    - "http://localhost"
    - "http://127.0.0.1"
  index_secret: "${INDEX_SECRET}"

weaviate:
  url: "http://weaviate:8080"
```

### `config/llm_config.yml`
```yaml
llm:
  provider: "openai"
  model: "gpt-4o"
  embedding_model: "text-embedding-3-small"
```

---

## 🔐 Secured Endpoints

### `POST /index`

Index a website (admin only)

**Headers**:
```
X-INDEX-TOKEN: your-secret-token
```

**Query param**:
```
website=https://example.com
```

---

### `POST /ask`

Ask a question (only for indexed websites)

**Request body**:
```json
{
  "q": "What services do you offer?",
  "website": "https://example.com"
}
```

---

### `GET /health`

Health check.

## 🧼 Cleanup

```bash
docker compose down --volumes
```

---

## 📄 License

MIT – Use it, modify it, deploy it.