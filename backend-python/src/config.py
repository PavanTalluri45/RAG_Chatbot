import os

from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# RAG Pipeline Configuration
TOP_K: int = int(os.getenv("TOP_K", "5"))
MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-3.1-flash-lite")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-2-preview")
PROMPT_CHARACTER_LIMIT: int = int(os.getenv("PROMPT_CHARACTER_LIMIT", "12000"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "30.0"))

# Cache Configuration
DOCUMENT_VERSION: str = os.getenv("DOCUMENT_VERSION", "v1")
REDIS_CACHE_TTL: int = int(os.getenv("REDIS_CACHE_TTL", "2592000"))  # 30 days
CACHE_PREFIX: str = os.getenv("CACHE_PREFIX", "rag")

# ChromaDB Configuration
COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "employee_handbook")
UPSERT_BATCH_SIZE: int = int(os.getenv("UPSERT_BATCH_SIZE", "100"))

# Logger Config
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Environment Keys
GOOGLE_EMBEDDING_API_KEY: str = os.getenv("GOOGLE_EMBEDDING_API_KEY")
GOOGLE_LLM_API_KEY: str = os.getenv("GOOGLE_LLM_API_KEY")
CHROMA_API_KEY: str = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT: str = os.getenv("CHROMA_TENANT")
CHROMA_DATABASE: str = os.getenv("CHROMA_DATABASE")
UPSTASH_REDIS_REST_URL: str = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN: str = os.getenv("UPSTASH_REDIS_REST_TOKEN")