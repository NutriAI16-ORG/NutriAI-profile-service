"""
Profile Service - Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "NutriAI Profile Service"
    DATABASE_URL: str = "postgresql://nutriai_user@localhost:5432/nutriai"
    APPLICATIONINSIGHTS_CONNECTION_STRING: str = ""
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
