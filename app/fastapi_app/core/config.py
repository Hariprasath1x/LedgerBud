"""Application settings for the FastAPI backend."""

import os
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "LedgerBud"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    mysql_database_url: str = Field(
        default="mysql+pymysql://root:password@127.0.0.1:3306/ledgerbud",
        validation_alias="MYSQL_DATABASE_URL",
    )
    jwt_secret_key: str = Field(default="change-me-in-production", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    use_firebase: bool = Field(default=False, validation_alias="USE_FIREBASE")
    firebase_api_key: str = Field(default="", validation_alias="FIREBASE_API_KEY")
    firebase_project_id: str = Field(default="", validation_alias="FIREBASE_PROJECT_ID")
    firebase_service_account_key: str = Field(default="", validation_alias="FIREBASE_SERVICE_ACCOUNT_KEY")

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8000", "http://localhost:8501"],
        validation_alias="CORS_ORIGINS",
    )
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    auto_create_tables: bool = Field(default=False, validation_alias="AUTO_CREATE_TABLES")
    groq_api_key: str = Field(default="", validation_alias="GROQ_API_KEY")

    @property
    def database_url(self) -> str:
        env_database_url = os.getenv("DATABASE_URL")
        if env_database_url and env_database_url.startswith(("mysql+", "mysql://")):
            return env_database_url
        if env_database_url and env_database_url.startswith(("postgresql+", "postgres://", "postgresql://")):
            return env_database_url
        return self.mysql_database_url

    @field_validator("cors_origins", mode="before")
    @classmethod
    def normalize_cors_origins(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return list(value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
