import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
custom_data_dir = os.getenv("DATA_DIR_PATH") or os.getenv("PERSISTENT_DATA_PATH")
DATA_DIR = Path(custom_data_dir) if custom_data_dir else (BASE_DIR / "data")
UPLOAD_DIR = DATA_DIR / "uploads"
VECTOR_DIR = DATA_DIR / "vector_store"
SAMPLE_DIR = BASE_DIR / "data" / "sample_documents"

# Ensure directories exist
for directory in [DATA_DIR, UPLOAD_DIR, VECTOR_DIR, SAMPLE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    APP_NAME: str = "Cognivora AI — Educational Content Generator"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*",
    ]

    # Database
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'cognivora.db'}"

    # Vector Storage
    CHROMA_PERSIST_DIRECTORY: str = str(VECTOR_DIR)
    CHROMA_COLLECTION_NAME: str = "cognivora_curriculum_chunks"

    # AI & Gemini Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    PRIMARY_MODEL: str = "gemini-2.5-flash"
    FAST_GENERATION_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "text-embedding-004"

    # Upload constraints
    MAX_FILE_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]

    # Ingestion & Chunking
    CHUNK_SIZE: int = 650
    CHUNK_OVERLAP: int = 120

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
