import os
import secrets
import warnings

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# Default Redis URL constant to avoid duplication
DEFAULT_REDIS_URL = "redis://localhost:6379/0"


def generate_secure_key():
    """Generate a secure random key for use when env var is not set."""
    return secrets.token_urlsafe(32)


class Settings(BaseSettings):

    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # Database
    database_url: str = Field(env="DATABASE_URL")

    # Redis
    redis_url: str = Field(default=DEFAULT_REDIS_URL, env="REDIS_URL")

    # Celery (using Redis for both broker and result backend in production)
    celery_broker_url: str = Field(default=DEFAULT_REDIS_URL, env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(
        default=DEFAULT_REDIS_URL, env="CELERY_RESULT_BACKEND"
    )

    # JWT
    secret_key: str = Field(env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # Password hashing
    pbkdf2_rounds: int = Field(default=1200000, env="PBKDF2_ROUNDS")

    # OAuth2 State
    oauth_state_secret: str = Field(env="OAUTH_STATE_SECRET")

    # Encryption
    encryption_password: str = Field(env="ENCRYPTION_PASSWORD")
    encryption_salt: str = Field(env="ENCRYPTION_SALT")

    # Vault - now optional with default empty value
    vault_url: str = Field(default="http://vault:8200", env="VAULT_URL")
    vault_token: str = Field(default="", env="VAULT_TOKEN")

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

    # API Keys for internal services - now optional with auto-generated defaults
    # These will generate secure random values if not set, allowing the app to start
    analytics_api_key: str = Field(default="dev-analytics-key", env="ANALYTICS_API_KEY")
    ingestion_api_key: str = Field(default="dev-ingestion-key", env="INGESTION_API_KEY")
    deduplication_api_key: str = Field(default="dev-deduplication-key", env="DEDUPLICATION_API_KEY")
    categorization_api_key: str = Field(default="dev-categorization-key", env="CATEGORIZATION_API_KEY")
    automation_api_key: str = Field(default="dev-automation-key", env="AUTOMATION_API_KEY")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    log_max_size: int = Field(default=10485760, env="LOG_MAX_SIZE")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")

    # Frontend URL for email templates
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")

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
        extra = "ignore"

    @field_validator(
        "secret_key",
        "encryption_password",
        "encryption_salt",
        "analytics_api_key",
        "ingestion_api_key", 
        "deduplication_api_key", 
        "categorization_api_key", 
        "automation_api_key",
        mode="before",
    )
    @classmethod
    def validate_critical_secrets(cls, v, info):
        """Validate that critical secrets are set in production."""
        env = os.getenv("ENVIRONMENT", "development")
        field_name = info.field_name
        
        # Skip validation for API keys - they have safe defaults
        if field_name in ["analytics_api_key", "ingestion_api_key", "deduplication_api_key", 
                       "categorization_api_key", "automation_api_key"]:
            if v is None:
                return f"dev-{field_name}"
            return v
            
        if env == "production":
            if v is None or (isinstance(v, str) and len(v.strip()) == 0):
                raise ValueError(
                    f"{field_name} is required and must be set to a secure value in production"
                )
            if isinstance(v, str) and (
                v.startswith("dev-")
                or v.startswith("CHANGE_")
                or v == "your-secret-key-here"
                or len(v) < 16
            ):
                raise ValueError(
                    f"{field_name} must be set to a secure value in production (not a placeholder)"
                )
        return v

    @field_validator(
        "analytics_api_key",
        "ingestion_api_key",
        "deduplication_api_key",
        "categorization_api_key",
        "automation_api_key",
        mode="after",
    )
    @classmethod
    def warn_about_auto_generated_keys(cls, v, info):
        """Warn if API keys are auto-generated (not explicitly set)."""
        field_name = info.field_name
        env = os.getenv("ENVIRONMENT", "development")
        env_var_name = field_name.upper()
        
        # Check if the value came from environment or was auto-generated
        env_value = os.getenv(env_var_name)
        if env_value is None and env == "production":
            warnings.warn(
                f"WARNING: {env_var_name} is not set. A random key was generated. "
                f"For production use, please set {env_var_name} explicitly to ensure "
                f"consistent authentication across service restarts.",
                RuntimeWarning,
                stacklevel=2
            )
        return v

    @field_validator(
        "cors_allow_origins",
        "cors_allow_methods",
        "cors_allow_headers",
        mode="before",
    )
    @classmethod
    def validate_cors_restrictions(cls, v, info):
        """Validate that CORS settings are not wildcard in production."""
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production":
            if isinstance(v, str) and v.strip() == "*":
                raise ValueError(
                    f"{info.field_name} cannot be '*' in production - must specify allowed {info.field_name.replace('cors_allow_', '')}"
                )
            if isinstance(v, list) and v == ["*"]:
                raise ValueError(
                    f"{info.field_name} cannot be ['*'] in production - must specify allowed {info.field_name.replace('cors_allow_', '')}"
                )
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v


# Create settings instance with error handling for better debugging
try:
    settings = Settings()
except Exception as e:
    import logging
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to load settings: {e}")
    logger.error("Environment variables check:")
    for key in ["DATABASE_URL", "SECRET_KEY", "ENCRYPTION_PASSWORD", "ENCRYPTION_SALT", "OAUTH_STATE_SECRET"]:
        value = os.getenv(key)
        logger.error(f"  {key}: {'SET' if value else 'NOT SET'}")
    raise
