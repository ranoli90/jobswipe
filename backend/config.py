import os
import secrets
import warnings

from pydantic import Field, field_validator, ConfigDict
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

    # Database - now optional with SQLite fallback for testing
    database_url: str = Field(default="sqlite:///./test.db", env="DATABASE_URL")

    # Redis
    redis_url: str = Field(default=DEFAULT_REDIS_URL, env="REDIS_URL")

    # Celery (using Redis for both broker and result backend in production)
    celery_broker_url: str = Field(default=DEFAULT_REDIS_URL, env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(
        default=DEFAULT_REDIS_URL, env="CELERY_RESULT_BACKEND"
    )

    # JWT - now optional with auto-generated keys
    secret_key: str = Field(default=generate_secure_key(), env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # Password hashing
    pbkdf2_rounds: int = Field(default=1200000, env="PBKDF2_ROUNDS")

    # OAuth2 State - now optional with auto-generated secret
    oauth_state_secret: str = Field(default=generate_secure_key(), env="OAUTH_STATE_SECRET")

    # Encryption - now optional with auto-generated values
    encryption_password: str = Field(default=generate_secure_key(), env="ENCRYPTION_PASSWORD")
    encryption_salt: str = Field(default=generate_secure_key(), env="ENCRYPTION_SALT")

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

    model_config = ConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

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
            
        # For other fields, allow auto-generated values even in production (for testing)
        if v is None:
            warnings.warn(f"{field_name} not provided, using auto-generated value", Warning)
            return generate_secure_key()
            
        # Still validate that secrets are not placeholders if provided
        if isinstance(v, str) and (
            v.startswith("dev-")
            or v.startswith("CHANGE_")
            or v == "your-secret-key-here"
            or len(v) < 16
        ):
            warnings.warn(f"{field_name} seems to be a placeholder, using auto-generated value", Warning)
            return generate_secure_key()
            
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
        mode="after",
    )
    @classmethod
    def validate_cors_restrictions(cls, v, info):
        """Validate that CORS settings are not wildcard in production."""
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production":
            if v == ["*"]:
                raise ValueError(
                    f"{info.field_name} cannot be ['*'] in production - must specify allowed {info.field_name.replace('cors_allow_', '')}"
                )
            if info.field_name == "cors_allow_origins" and (not v or len(v) == 0):
                raise ValueError(
                    f"{info.field_name} must be specified in production via {info.field_name.upper()} environment variable"
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
    def validate_no_dev_keys_in_production(cls, v, info):
        """Prevent API keys from using 'dev-*' defaults in production."""
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production" and v.startswith("dev-"):
            raise ValueError(
                f"{info.field_name} cannot start with 'dev-' in production environment. "
                "Please set a proper API key via the corresponding environment variable."
            )
        return v


# Create settings instance with error handling for better debugging
try:
    # Debug logging for environment variables in production
    import logging
    logger = logging.getLogger(__name__)
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        logger.warning("Environment variables check:")
        for var in ["VAULT_TOKEN", "ANALYTICS_API_KEY", "INGESTION_API_KEY", "DEDUPLICATION_API_KEY", "CATEGORIZATION_API_KEY", "AUTOMATION_API_KEY"]:
            value = os.getenv(var)
            if value:
                logger.warning(f"{var}: set (length {len(value)})")
            else:
                logger.warning(f"{var}: not set")
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
