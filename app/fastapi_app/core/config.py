"""Application settings for the FastAPI backend."""

import os
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "LedgerBud"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    mysql_database_url: str = Field(
        default="mysql+pymysql://root:password@127.0.0.1:3306/ledgerbud",
        validation_alias="MYSQL_DATABASE_URL",
    )
    database_url_env: str | None = Field(default=None, validation_alias="DATABASE_URL")

    use_firebase: bool = Field(default=False, validation_alias="USE_FIREBASE")
    firebase_api_key: str = Field(default="", validation_alias="FIREBASE_API_KEY")
    firebase_project_id: str = Field(default="", validation_alias="FIREBASE_PROJECT_ID")
    firebase_service_account_key: str = Field(default="", validation_alias="FIREBASE_SERVICE_ACCOUNT_KEY")

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8501",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:8501",
        ],
        validation_alias="CORS_ORIGINS",
    )
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    auto_create_tables: bool = Field(default=False, validation_alias="AUTO_CREATE_TABLES")
    groq_api_key: str = Field(default="", validation_alias="GROQ_API_KEY")
    groq_model: str = Field(default="openai/gpt-oss-120b", validation_alias="GROQ_MODEL")
    max_upload_size_mb: int = Field(default=16, validation_alias="MAX_UPLOAD_SIZE_MB")

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def database_url(self) -> str:
        env_database_url = self.database_url_env or os.getenv("DATABASE_URL")
        if env_database_url:
            cleaned = env_database_url.strip()
            if cleaned.startswith("postgres://"):
                return cleaned.replace("postgres://", "postgresql://", 1)
            if cleaned.startswith(("postgresql+", "postgresql://", "mysql+", "mysql://", "sqlite")):
                return cleaned
        return self.mysql_database_url

    @field_validator("cors_origins", mode="before")
    @classmethod
    def normalize_cors_origins(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            origins = [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        elif isinstance(value, (list, tuple, set)):
            origins = [str(origin).strip().rstrip("/") for origin in value if str(origin).strip()]
        else:
            origins = list(value)
        # Disallow wildcard '*' origin because FastAPI uses allow_credentials=True
        if "*" in origins:
            raise ValueError(
                "Wildcard '*' origin is not permitted when credentials are supported. "
                "Specify explicit trusted origins via CORS_ORIGINS."
            )
        return origins


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
