from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(env_file=".env")
    
    # Database
    database_url: str = "postgresql://user:password@db:5432/desensitization"
    
    # File upload
    max_file_size: int = 52428800  # 50MB in bytes
    upload_dir: str = "/app/uploads"
    
    # NLP
    nlp_model_path: str = "/app/models/chinese_ner"
    
    # Logging
    log_level: str = "INFO"
    
    # CORS
    cors_origins: str = "http://localhost:80"


settings = Settings()
