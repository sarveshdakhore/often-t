import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Travel Itinerary API"
    API_PREFIX: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/traveldb")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # OpenRouter Settings
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_KEY_HERE")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    # Specify a model available on OpenRouter (e.g., a free one)
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
    # Optional: Add site name for OpenRouter headers
    OPENROUTER_SITE_NAME: str = os.getenv("OPENROUTER_SITE_NAME", "YourAppName")

    # Add other settings as needed

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
