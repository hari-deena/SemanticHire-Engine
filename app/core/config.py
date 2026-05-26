from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):

    # =========================
    # 🔥 APP CONFIG
    # =========================
    APP_ENV: str = "development"
    APP_NAME: str = "job_ai"


    # =========================
    # 🔥 REDIS (Cache + Celery)
    # =========================
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0


    # =========================
    # 🔥 CELERY
    # =========================
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str


    # =========================
    # 🔥 CHROMA VECTOR DB
    # =========================
    CHROMA_HOST: str
    CHROMA_PORT: int
    CHROMA_COLLECTION_NAME: str


    # =========================
    # 🔥 OPENAI EMBEDDINGS
    # =========================
    OPENAI_API_KEY: str
    EMBEDDING_MODEL: str
    EMBEDDING_TIMEOUT: int = 10


    # =========================
    # 🔥 HUGGINGFACE FALLBACK
    # =========================
    EMBEDDING_MODEL_HF: str


    # =========================
    # 🔥 CACHE
    # =========================
    EMBEDDING_CACHE_TTL: int = 86400


    # =========================
    # 🔥 PIPELINE LIMITS
    # =========================
    MAX_CHUNKS: int = 200
    MAX_TEXT_LENGTH: int = 3000


    # =========================
    # 🔥 VALIDATION CONTROL
    # =========================
    STRICT_EMBEDDING_VALIDATION: bool = True
    
    # =========================
    # 🔥 GROQ LLM CONFIG
    GROQ_API_KEY: str
    GROQ_MODEL: str
    FALLBACK_GROQ_MODEL: str
    
    # =========================
    # DB CONFIG
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_NAME: str
    DB_PORT: int = 3306


    # =========================
    # 🔥 Pydantic Settings Config
    # =========================
    class Config:
        env_file = ".env"
        case_sensitive = True


# 🔥 Cached settings instance (IMPORTANT)
@lru_cache()
def get_settings() -> Settings:
    return Settings()


# 🔥 Global usage (simple access)
settings = get_settings()