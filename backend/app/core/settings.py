from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime configuration for TMI OS."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_ENV: Literal["development", "test", "production"] = "development"
    API_NAME: str = "TMI API"
    API_VERSION: str = "0.3.0"
    LOG_LEVEL: str = "INFO"

    AUTH_VIEWER_API_KEY: SecretStr = Field(
        default=SecretStr("dev-viewer-key")
    )
    AUTH_OPERATOR_API_KEY: SecretStr = Field(
        default=SecretStr("dev-operator-key")
    )
    AUTH_REVIEWER_API_KEY: SecretStr = Field(
        default=SecretStr("dev-reviewer-key")
    )
    AUTH_ADMIN_API_KEY: SecretStr = Field(
        default=SecretStr("dev-admin-key")
    )
    AUTH_READ_RATE_LIMIT_PER_MINUTE: int = Field(
        default=120,
        ge=1,
        le=10000,
    )
    AUTH_WRITE_RATE_LIMIT_PER_MINUTE: int = Field(
        default=30,
        ge=1,
        le=10000,
    )

    AI_PROVIDER: Literal["ollama"] = "ollama"
    AI_PRIMARY_MODEL: str = "qwen2.5:3b"
    AI_FALLBACK_MODELS: str = ""
    AI_TEMPERATURE: float = Field(default=0.1, ge=0.0, le=2.0)
    AI_MAX_OUTPUT_TOKENS: int = Field(default=2000, ge=1, le=32768)
    AI_CONTEXT_WINDOW: int = Field(default=8192, ge=1024, le=131072)
    AI_MAX_RETRIES: int = Field(default=0, ge=0, le=10)
    AI_RETRY_DELAY_SECONDS: float = Field(default=1.0, ge=0.0, le=60.0)
    AI_CACHE_ENABLED: bool = True
    AI_CACHE_TTL_SECONDS: int = Field(default=3600, ge=0)
    AI_CACHE_MAX_ITEMS: int = Field(default=500, ge=1)
    AI_PROMPT_MAX_CHARACTERS: int = Field(default=6000, ge=1000)

    OLLAMA_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_CONNECT_TIMEOUT: float = Field(default=10.0, ge=1.0)
    OLLAMA_READ_TIMEOUT: float = Field(default=180.0, ge=10.0)
    OLLAMA_KEEP_ALIVE: str = "10m"

    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "tmi"
    POSTGRES_USER: str = "tmi"
    POSTGRES_PASSWORD: SecretStr = Field(
        default=SecretStr("ChangeThisPassword123!")
    )

    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_API_KEY: SecretStr = Field(default=SecretStr(""))
    QDRANT_COLLECTION_NAME: str = "tmi_campaigns"
    QDRANT_VECTOR_SIZE: int = Field(default=768, ge=1)
    QDRANT_DISTANCE: Literal["cosine", "dot", "euclid"] = "cosine"
    QDRANT_TIMEOUT_SECONDS: float = Field(default=30.0, ge=1.0, le=120.0)

    SEARXNG_URL: str = "http://tmi-searxng:8080"
    SEARXNG_TIMEOUT: int = Field(default=30, ge=1, le=120)

    SERPER_API_KEY: SecretStr = Field(default=SecretStr(""))
    SERPER_URL: str = "https://google.serper.dev/search"
    SERPER_TIMEOUT: int = Field(default=30, ge=1, le=120)

    PEXELS_API_KEY: SecretStr = Field(default=SecretStr(""))
    PIXABAY_API_KEY: SecretStr = Field(default=SecretStr(""))
    STOCK_MEDIA_MAX_SEARCHES: int = Field(default=3, ge=1, le=3)
    STOCK_MEDIA_MAX_ASSETS: int = Field(default=6, ge=1, le=6)
    STOCK_MEDIA_TIMEOUT_SECONDS: int = Field(default=30, ge=5, le=120)

    REDIS_PASSWORD: SecretStr = Field(default=SecretStr(""))
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = Field(default=6379, ge=1, le=65535)
    READINESS_TIMEOUT_SECONDS: float = Field(default=3.0, ge=0.5, le=30.0)

    DB_POOL_SIZE: int = Field(default=10, ge=1, le=100)
    DB_MAX_OVERFLOW: int = Field(default=20, ge=0, le=200)
    DB_POOL_RECYCLE_SECONDS: int = Field(default=1800, ge=60)

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.strip().upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

        if normalized not in allowed:
            raise ValueError(
                f"LOG_LEVEL must be one of {sorted(allowed)}"
            )

        return normalized

    @field_validator(
        "AI_PRIMARY_MODEL",
        "OLLAMA_MODEL",
        "OLLAMA_EMBEDDING_MODEL",
        "OLLAMA_KEEP_ALIVE",
        "QDRANT_URL",
        "QDRANT_COLLECTION_NAME",
    )
    @classmethod
    def validate_non_empty_string(cls, value: str) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError("Value cannot be empty.")

        return normalized

    @property
    def database_url(self) -> str:
        password = self.POSTGRES_PASSWORD.get_secret_value()

        return (
            "postgresql+psycopg2://"
            f"{self.POSTGRES_USER}:{password}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def serper_api_key_value(self) -> str:
        return self.SERPER_API_KEY.get_secret_value()

    @property
    def ai_models(self) -> list[str]:
        models = [self.AI_PRIMARY_MODEL]

        fallback_models = [
            model.strip()
            for model in self.AI_FALLBACK_MODELS.split(",")
            if model.strip()
        ]

        for model in fallback_models:
            if model not in models:
                models.append(model)

        return models

    @property
    def api_keys_by_role(self) -> dict[str, str]:
        keys = {
            "viewer": self.AUTH_VIEWER_API_KEY.get_secret_value(),
            "operator": self.AUTH_OPERATOR_API_KEY.get_secret_value(),
            "reviewer": self.AUTH_REVIEWER_API_KEY.get_secret_value(),
            "admin": self.AUTH_ADMIN_API_KEY.get_secret_value(),
        }
        if self.APP_ENV == "production":
            invalid = [
                role
                for role, key in keys.items()
                if (
                    not key.strip()
                    or key.startswith("dev-")
                    or key.startswith("REPLACE_WITH_")
                )
            ]
            if invalid:
                raise ValueError(
                    "Production API keys must be configured for: "
                    + ", ".join(invalid)
                )
        return keys

    def validate_production_secrets(self) -> None:
        if self.APP_ENV != "production":
            return
        self.api_keys_by_role
        invalid: list[str] = []
        postgres_password = self.POSTGRES_PASSWORD.get_secret_value()
        if (
            postgres_password in {"", "ChangeThisPassword123!"}
            or postgres_password.startswith("REPLACE_WITH_")
        ):
            invalid.append("POSTGRES_PASSWORD")
        qdrant_key = self.QDRANT_API_KEY.get_secret_value().strip()
        if not qdrant_key or qdrant_key.startswith("REPLACE_WITH_"):
            invalid.append("QDRANT_API_KEY")
        redis_password = self.REDIS_PASSWORD.get_secret_value().strip()
        if (
            not redis_password
            or redis_password.startswith("REPLACE_WITH_")
        ):
            invalid.append("REDIS_PASSWORD")
        if invalid:
            raise ValueError(
                "Production secrets must be configured for: "
                + ", ".join(invalid)
            )


@lru_cache
def get_settings() -> Settings:
    configured = Settings()
    configured.validate_production_secrets()
    return configured


settings = get_settings()
