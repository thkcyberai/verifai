"""
Core configuration management.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    enable_real_adapters: bool = False
    
    openai_api_key: str = ""
    factiai_api_key: str = ""
    brave_search_api_key: str = ""
    
    database_url: str = "postgresql://factiai:factiai_pass@localhost:5432/factiai_db"
    redis_url: str = "redis://localhost:6379/0"
    
    jwt_secret: str = "dev-secret-key"
    jwt_algorithm: str = "HS256"
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:19006,exp://localhost:19000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
