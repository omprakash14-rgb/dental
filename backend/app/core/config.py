import os
from typing import List

class Settings:
    PROJECT_NAME: str = "DentalAI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Cryptography and Token Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dentalai-secret-jwt-key-2026-prod-secure-38491823901")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://dentalai:dentalai_password@localhost:5432/dentalai"
    )
    SQLITE_FALLBACK_URL: str = "sqlite:///./dentalai.db"
    
    # CORS
    raw_cors: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://localhost:8000"
    )
    CORS_ORIGINS: List[str] = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]
    
    # Rate Limiting
    RATE_LIMIT_LOGIN: str = os.getenv("RATE_LIMIT_LOGIN", "10/minute")
    RATE_LIMIT_SCREENING: str = os.getenv("RATE_LIMIT_SCREENING", "60/minute")
    
    # Storage
    UPLOADS_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
    MODELS_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "models")

settings = Settings()

