from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5434/proveniq_anchors"
    
    # Ledger Integration
    ledger_api_url: str = "http://localhost:8006/api/v1"
    ledger_api_key: str = ""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8005
    debug: bool = True
    
    # Security
    allowed_origins: str = "http://localhost:3000,http://localhost:9003"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
