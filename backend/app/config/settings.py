from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Google AI Configuration
    google_api_key: str
    
    # Weather API Configuration
    openweather_api_key: str
    
    
    # App Configuration
    app_name: str = "TBuddy"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Model Configuration
    model_name: str = "gemini-2.5-pro"
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()