import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load .env variables if available
load_dotenv()

class Config:
    def __init__(self):
        config_path = Path(__file__).parent.parent / "config"

        try:
            with open(config_path / "application.yml") as f:
                full_app_config = yaml.safe_load(f)
                self.app_config = full_app_config.get("app", {})
                self.weaviate_config = full_app_config.get("weaviate", {})
        except Exception as e:
            raise RuntimeError(f"Failed to load application.yml: {e}")

        try:
            with open(config_path / "llm_config.yml") as f:
                self.llm_config = yaml.safe_load(f).get("llm", {})
        except Exception as e:
            raise RuntimeError(f"Failed to load llm_config.yml: {e}")

        # Validate and assign app config
        self.ALLOWED_ORIGINS = self._validate_origins(self.app_config.get("allowed_origins", []))
        self.INDEX_SECRET = os.getenv("INDEX_SECRET", "")

        # Weaviate
        self.WEAVIATE_URL = self.weaviate_config.get("url", "http://localhost:8080")
        self.WEAVIATE_GRPC_PORT = self.weaviate_config.get("grpc_port", 50051)

        # LLM
        self.LLM_MODEL = self.llm_config.get("model", "gpt-4")
        self.LLM_EMBEDDING_MODEL = self.llm_config.get("embedding_model", "text-embedding-3-small")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

        if not self.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set in .env or llm_config.yml")

    def _validate_origins(self, origins):
        if not isinstance(origins, list):
            raise ValueError("allowed_origins must be a list in application.yml")
        return origins


config = Config()
