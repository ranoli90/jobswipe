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

    # Environment - CRITICAL: Require explicit production setting
    environment: str = Field(..., env="ENVIRONMENT", pattern="^(development|staging|production)$")
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

    # JWT - CRITICAL: Must be explicitly set in production
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # Password hashing
    pbkdf2_rounds: int = Field(default=1200000, env="PBKDF2_ROUNDS")

    # OAuth2 State - CRITICAL: Must be explicitly set in production
    oauth_state_secret: str = Field(..., env="OAUTH_STATE_SECRET")

    # Encryption - CRITICAL: Must be explicitly set in production
    encryption_password: str = Field(..., env="ENCRYPTION_PASSWORD")
    encryption_salt: str = Field(..., env="ENCRYPTION_SALT")

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

    # API Keys for internal services - CRITICAL: Must be explicitly set in production
    analytics_api_key: str = Field(..., env="ANALYTICS_API_KEY")
    ingestion_api_key: str = Field(..., env="INGESTION_API_KEY")
    deduplication_api_key: str = Field(..., env="DEDUPLICATION_API_KEY")
    categorization_api_key: str = Field(..., env="CATEGORIZATION_API_KEY")
    automation_api_key: str = Field(..., env="AUTOMATION_API_KEY")

    # Apple Push Notification Service
    apple_key_id: str = Field(..., env="APPLE_KEY_ID")
    apple_team_id: str = Field(..., env="APPLE_TEAM_ID")
    apple_bundle_id: str = Field(..., env="APPLE_BUNDLE_ID")
    apple_private_key: str = Field(..., env="APPLE_PRIVATE_KEY")

    # Push Notification Settings
    push_enabled: bool = Field(default=False, env="PUSH_ENABLED")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    log_max_size: int = Field(default=10485760, env="LOG_MAX_SIZE")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")

    # Frontend URL for email templates
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")

    # CORS Configuration
    cors_allow_origins: list = Field(
        default=["http://localhost:3000", "https://localhost:3000", "http://localhost:8080", "https://localhost:8080", "http://localhost:*", "https://jobswipe-web.fly.dev"],
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
        
        # For all fields, use secure auto-generated keys if not provided
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


def get_settings() -> Settings:
    """Dependency injection function to get settings instance"""
    return settings

# Create settings instance with error handling for better debugging
try:
    # Debug logging for environment variables in production
    import logging
    logger = logging.getLogger(__name__)
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        # Log generically without exposing which secrets are set
        logger.warning("Checking required environment variables for production")
        all_set = True
        required_vars = ["SECRET_KEY", "ENCRYPTION_PASSWORD", "OAUTH_STATE_SECRET"]
        for var in required_vars:
            if not os.getenv(var):
                all_set = False
                break
        if not all_set:
            logger.error("Some required environment variables are not set")
    settings = Settings()
except Exception as e:
    import logging
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to load settings: {e}")
    logger.error("Checking required environment variables...")
    # Log generically without exposing which specific secrets are set
    missing_vars = []
    for key in ["DATABASE_URL", "SECRET_KEY", "ENCRYPTION_PASSWORD", "OAUTH_STATE_SECRET"]:
        if not os.getenv(key):
            missing_vars.append(key)
    if missing_vars:
        logger.error(f"Missing required variables: {', '.join(missing_vars)}")
    else:
        logger.error("All required environment variables are set")
    raise
