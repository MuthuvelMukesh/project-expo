"""
CampusIQ Core Configuration
Loads environment variables and provides app-wide settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "CampusIQ"
    DEBUG: bool = True
    SECRET_KEY: str = "campusiq-dev-secret-key-change-in-production"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://campusiq:campusiq_secret@localhost:5432/campusiq"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Ollama (Local LLM)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma:2b"

    # LLM Provider (ollama | google)
    LLM_PROVIDER: str = "ollama"
    GOOGLE_API_KEY: str = ""
    GOOGLE_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    GOOGLE_MODEL: str = "gemini-1.5-flash"

    # Conversational Ops AI (Gemini key pools)
    GEMINI_NLP_KEYS: str = ""
    GEMINI_PREDICTIONS_KEYS: str = ""
    GEMINI_FINANCE_KEYS: str = ""
    GEMINI_HR_KEYS: str = ""
    GEMINI_CHAT_KEYS: str = ""
    GEMINI_RETRY_ETA_SECONDS: int = 60

    # Conversational Ops Controls
    OPS_CONFIDENCE_THRESHOLD: float = 0.75
    OPS_MAX_PREVIEW_ROWS: int = 50
    OPS_SENIOR_ROLES: str = "admin"
    OPS_REQUIRE_2FA_HIGH_RISK: bool = True
    
    # ML
    MODEL_PATH: str = "app/ml/models"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @staticmethod
    def _split_keys(raw: str) -> List[str]:
        return [item.strip() for item in (raw or "").split(",") if item.strip()]

    @property
    def GEMINI_KEY_POOLS(self) -> dict[str, List[str]]:
        return {
            "nlp": self._split_keys(self.GEMINI_NLP_KEYS),
            "predictions": self._split_keys(self.GEMINI_PREDICTIONS_KEYS),
            "finance": self._split_keys(self.GEMINI_FINANCE_KEYS),
            "hr": self._split_keys(self.GEMINI_HR_KEYS),
            "chat": self._split_keys(self.GEMINI_CHAT_KEYS),
        }

    @property
    def OPS_SENIOR_ROLE_SET(self) -> set[str]:
        return set(self._split_keys(self.OPS_SENIOR_ROLES))


@lru_cache()
def get_settings() -> Settings:
    return Settings()
