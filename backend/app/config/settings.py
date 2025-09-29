from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Google AI Configuration
    google_api_key: str
    
    # Weather API Configuration
    openweather_api_key: str

    openroute_api_key: str

    openweb_ninja_api_key: Optional[str] = None 
    openweb_ninja_base_url: str = "https://api.openwebninja.com/realtime-events-data/search-events"
    openweb_ninja_timeout: float = 30.0
    
    
    # App Configuration
    app_name: str = "TBuddy"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Model Configuration
    model_name: str = "gemini-2.5-pro"
    temperature: float = 0.1
    max_tokens: Optional[int] = None

    # Event Service Configuration
    events_fallback_enabled: bool = True
    events_cache_ttl: int = 3600  # 1 hour cache
    events_max_results: int = 100
    events_default_days_ahead: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()