from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Relayline Social Studio"
    environment: str = "development"
    database_url: str = "sqlite:///./social_studio.db"
    token_encryption_key: str = ""
    fake_social_base_url: str = "http://localhost:8090"
    social_webhook_secret: str = "development-only-webhook-secret"
    frontend_origin: str = "http://localhost:5173"
    max_publish_attempts: int = Field(default=4, ge=1, le=10)
    worker_poll_seconds: float = Field(default=1.0, ge=0.1, le=60)
    publish_lease_seconds: int = Field(default=60, ge=5, le=3600)
    retry_max_seconds: int = Field(default=3600, ge=1)
    upload_max_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)
    webhook_tolerance_seconds: int = Field(default=300, ge=1)
    data_dir: Path = Path(".")

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def generated_dir(self) -> Path:
        return self.data_dir / "generated" / "campaigns"


@lru_cache
def get_settings() -> Settings:
    return Settings()
