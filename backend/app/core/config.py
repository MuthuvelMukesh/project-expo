"""
CampusIQ Core Configuration
Loads environment variables and provides app-wide settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    DEBUG: bool = False
    APP_NAME: str = "CampusIQ"

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours — full work day

    # LLM — supports OpenRouter (default) or Google Gemini native
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "google/gemini-2.0-flash-001"
    GEMINI_TEMPERATURE_JSON: float = 0.1
    GEMINI_TEMPERATURE_CHAT: float = 0.4
    GEMINI_MAX_OUTPUT_TOKENS: int = 2048
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_RETRY_DELAY: float = 2.0
    LLM_PROVIDER: str = "openrouter"  # "openrouter" or "gemini"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai"

    # ML
    MODEL_PATH: str = "app/ml/models/grade_predictor.joblib"

    # Conversational ops — direct execution thresholds
    OPS_CONFIDENCE_THRESHOLD: float = 0.75
    OPS_MAX_PREVIEW_ROWS: int = 50
    RISK_HIGH_IMPACT_COUNT: int = 50
    RISK_MEDIUM_IMPACT_COUNT: int = 10

    # Frontend static files (production single-server)
    SERVE_FRONTEND: bool = True
    FRONTEND_DIST_PATH: str = "../frontend/dist"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
