import yaml
from pathlib import Path
import os

class Config:
    def __init__(self):
        with open(Path(__file__).parent.parent / "config/application.yml") as f:
            full_app_config = yaml.safe_load(f)
            self.app_config = full_app_config.get("app", {})
            self.weaviate_config = full_app_config.get("weaviate", {})

        with open(Path(__file__).parent.parent / "config/llm_config.yml") as f:
            self.llm_config = yaml.safe_load(f).get("llm", {})

        self.WEAVIATE_URL = self.weaviate_config.get("url", "http://localhost:8080")
        self.WEAVIATE_GRPC_PORT = self.weaviate_config.get("grpc_port", 50051)
        self.ALLOWED_ORIGINS = self.app_config.get("allowed_origins", [])

        self.LLM_MODEL = self.llm_config.get("model", "gpt-4")
        self.LLM_EMBEDDING_MODEL = self.llm_config.get("embedding_model", "text-embedding-3-small")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or self.llm_config.get("api_key", "")

config = Config()
