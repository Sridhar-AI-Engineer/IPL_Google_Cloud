"""Production-ready configuration management."""
import os
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # ==================== DATABASE ====================
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg2://user:password@localhost:5432/ipl_agentic_coach"
    )
    sqlite_db_path: str = "./ipl_agentic_coach/backend/historical_matches.db"
    db_echo: bool = False
    db_pool_size: int = 20
    db_max_overflow: int = 40
    db_pool_recycle: int = 3600

    # ==================== JWT & SECURITY ====================
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production-min-32-chars")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    refresh_token_expiration_days: int = 7
    token_audience: str = "ipl-agentic-coach"
    token_issuer: str = "ipl-agentic-coach-backend"

    # ==================== OAUTH2 ====================
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    facebook_client_id: str = os.getenv("FACEBOOK_CLIENT_ID", "")
    facebook_client_secret: str = os.getenv("FACEBOOK_CLIENT_SECRET", "")

    # ==================== FIREBASE ====================
    firebase_project_id: str = os.getenv("FIREBASE_PROJECT_ID", "")
    firebase_enabled: bool = bool(firebase_project_id)

    # ==================== RATE LIMITING ====================
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 3600
    rate_limit_storage: Literal["memory", "redis"] = "memory"

    # ==================== REDIS ====================
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_enabled: bool = os.getenv("REDIS_ENABLED", "false").lower() == "true"

    # ==================== ERROR TRACKING ====================
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    sentry_enabled: bool = bool(sentry_dsn) and os.getenv("SENTRY_ENABLED", "true").lower() == "true"
    sentry_traces_sample_rate: float = 0.1
    sentry_environment: str = os.getenv("SENTRY_ENVIRONMENT", "development")

    # ==================== LOGGING ====================
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: Literal["json", "text"] = "json"  # type: ignore
    log_file_path: str = "./logs/app.log"

    # ==================== AI/ML ====================
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    tactical_pipeline_mode: Literal["auto", "langchain", "langgraph", "local"] = "auto"  # type: ignore
    langchain_llm_model: str = "gemini-2.0-flash"

    # ==================== CLOUD DEPLOYMENT ====================
    project_id: str | None = None
    gemini_model: str = "gemini-2.0-flash"

    # ==================== API ====================
    api_version: str = "v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    allow_credentials: bool = True

    # ==================== ADMIN ====================
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "change-this")

    # ==================== MONITORING ====================
    prometheus_enabled: bool = os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true"
    prometheus_port: int = 9090

    # ==================== DEPLOYMENT ====================
    env: Literal["development", "staging", "production"] = os.getenv("ENV", "development")  # type: ignore
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    workers: int = int(os.getenv("WORKERS", "4"))
    uvicorn_host: str = os.getenv("UVICORN_HOST", "0.0.0.0")
    uvicorn_port: int = int(os.getenv("UVICORN_PORT", "8000"))

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
