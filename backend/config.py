import os

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # Database
    database_url: str = Field(env="DATABASE_URL")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Celery (using Redis for both broker and result backend in production)
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0", env="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND"
    )

    # JWT
    secret_key: str = Field(env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Password hashing
    pbkdf2_rounds: int = Field(default=1200000, env="PBKDF2_ROUNDS")

    # OAuth2 State
    oauth_state_secret: str = Field(env="OAUTH_STATE_SECRET")

    # Encryption
    encryption_password: str = Field(env="ENCRYPTION_PASSWORD")
    encryption_salt: str = Field(env="ENCRYPTION_SALT")

    # Vault
    vault_url: str = Field(default="http://vault:8200", env="VAULT_URL")
    vault_token: str = Field(env="VAULT_TOKEN")

    # AI Services
    ollama_base_url: str = Field(
        default="http://localhost:11434/v1", env="OLLAMA_BASE_URL"
    )
    ollama_model: str = Field(default="llama3.2:3b", env="OLLAMA_MODEL")
    ollama_embedding_model: str = Field(
        default="nomic-embed-text", env="OLLAMA_EMBEDDING_MODEL"
    )
    ollama_temperature: float = Field(default=0.1, env="OLLAMA_TEMPERATURE")
    ollama_max_tokens: int = Field(default=2000, env="OLLAMA_MAX_TOKENS")

    # API Keys for internal services
    analytics_api_key: str = Field(env="ANALYTICS_API_KEY")
    ingestion_api_key: str = Field(env="INGESTION_API_KEY")
    deduplication_api_key: str = Field(env="DEDUPLICATION_API_KEY")
    categorization_api_key: str = Field(env="CATEGORIZATION_API_KEY")
    automation_api_key: str = Field(env="AUTOMATION_API_KEY")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    log_max_size: int = Field(default=10485760, env="LOG_MAX_SIZE")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")

    # CORS Configuration
    cors_allow_origins: list = Field(
        default=["http://localhost:3000", "https://localhost:3000"],
        env="CORS_ALLOW_ORIGINS",
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: list = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        env="CORS_ALLOW_METHODS",
    )
    cors_allow_headers: list = Field(
        default=["Authorization", "Content-Type", "X-Request-ID"],
        env="CORS_ALLOW_HEADERS",
    )

    class Config:
        env_file = os.getenv("ENV_FILE", ".env")
        env_file_encoding = "utf-8"

    @validator(
        "secret_key",
        "encryption_password",
        "encryption_salt",
        "analytics_api_key",
        "ingestion_api_key",
        "deduplication_api_key",
        "categorization_api_key",
        "automation_api_key",
        pre=True,
        always=True,
    )
    def validate_secrets(cls, v, field):
        if cls.environment == "production" and (
            v is None
            or v.startswith("dev-")
            or v.startswith("CHANGE_")
            or len(v.strip()) == 0
        ):
            raise ValueError(
                f"{field.name} must be set to a secure value in production"
            )
        return v

    @validator(
        "cors_allow_origins", "cors_allow_methods", "cors_allow_headers", pre=True
    )
    def validate_cors_restrictions(cls, v, field):
        """Validate that CORS settings are not wildcard in production."""
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production":
            if isinstance(v, str) and v.strip() == "*":
                raise ValueError(
                    f"{field.name} cannot be '*' in production - must specify allowed {field.name.replace('cors_allow_', '')}"
                )
            if isinstance(v, list) and v == ["*"]:
                raise ValueError(
                    f"{field.name} cannot be ['*'] in production - must specify allowed {field.name.replace('cors_allow_', '')}"
                )
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v


# Create settings instance
settings = Settings()
