# Website-Aware AI Chatbot Backend

This project is a Dockerized FastAPI backend that powers a website-aware AI chatbot. It crawls and indexes website content into a vector database (Weaviate), then uses OpenAI's GPT model to answer user questions **based only on that site's content**.

---

## ✨ Features

- 🔎 Website crawler and indexer (via `/index`)
- 🤖 Ask questions securely (via `/ask`, POST)
- ⚡ Fast Weaviate vector search
- 🧠 GPT-4o (or GPT-3.5/4) answering based on context
- 🐳 Docker + Docker Compose
- 🔐 CORS-enabled API for frontend use
- 📦 Ready to deploy or integrate

---

## 🧱 Folder Structure

```
chatbot/
├── app/
│   ├── main.py                 # FastAPI app
│   ├── chatbot.py              # GPT logic + Weaviate query
│   ├── vectorizer.py           # Embeds + uploads site content
│   ├── website_loader.py       # Crawls a website
│   ├── weaviate_client.py      # Connects and manages schema
│   ├── config.py               # Loads from application.yml + llm_config.yml
│   ├── logger.py               # Logging utility
│   └── __init__.py
├── config/
│   ├── application.yml         # Port, CORS, Weaviate URL
│   └── llm_config.yml          # OpenAI model + key
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .gitignore
```

---

## 🚀 Quick Start

### 1. 🛠️ Prerequisites

- Docker + Docker Compose
- OpenAI API key

---

### 2. 🧪 Setup

Edit `config/llm_config.yml` and replace:

```yaml
api_key: "YOUR_OPENAI_API_KEY"
```

> ✅ Never commit your actual API key — `.gitignore` already ignores it.

---

### 3. 🐳 Run Everything

```bash
docker compose up --build
```

- Chatbot: [http://localhost:8000](http://localhost:8000)
- Weaviate: [http://localhost:8080](http://localhost:8080)

---

## 🔌 API Endpoints

### `/index?website=https://example.com`

Crawls and indexes website pages into Weaviate.

**Method:** `POST`

---

### `/ask`

Ask a question related to the website.

**Method:** `POST`  
**Body:**

```json
{
  "q": "What is your return policy?",
  "website": "https://example.com"
}
```

---

## 📚 Notes

- The chatbot only answers based on indexed website content.
- Vectors are stored in the `WebContent` class inside Weaviate.
- Embeddings are created using `text-embedding-3-small`.

---

## 🧼 Cleaning & Reset

To remove stored vector data:

```bash
docker compose down -v
```

---

## 🔐 Security

- No secrets in Git
- API served via POST only
- CORS is enabled for local use (customizable)

---

## 📦 Deployment

You can deploy using any container platform (Render, Fly.io, Railway, etc.) with the same `Dockerfile`.

---

## 🙌 Credits

- [FastAPI](https://fastapi.tiangolo.com/)
- [Weaviate](https://weaviate.io/)
- [OpenAI API](https://platform.openai.com/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)

---

MIT License.
