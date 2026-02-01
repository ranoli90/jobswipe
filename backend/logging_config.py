"""
Structured Logging Configuration

Provides centralized logging with:
- Structured JSON logging format
- Configurable log levels per environment
- Integration with ELK stack (Elasticsearch, Logstash, Kibana)
- Integration with Datadog (optional)
- Log correlation IDs for request tracing
- Separate loggers for different components (api, workers, services)
"""

import json
import logging
import logging.config
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger


class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation ID to log records"""
    
    def __init__(self, name: str = ""):
        super().__init__(name)
        self._correlation_id = None
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            record.correlation_id = record.correlation_id
        else:
            record.correlation_id = getattr(
                CorrelationIdFilter, "_thread_correlation_id", "unknown"
            )
        
        # Add service name
        record.service = getattr(record, "service", "jobswipe")
        
        # Add environment
        record.environment = os.getenv("ENVIRONMENT", "development")
        
        return True
    
    @classmethod
    def set_correlation_id(cls, correlation_id: str):
        """Set correlation ID for current thread"""
        cls._thread_correlation_id = correlation_id
    
    @classmethod
    def get_correlation_id(cls) -> str:
        """Get correlation ID for current thread"""
        return getattr(cls, "_thread_correlation_id", "unknown")
    
    @classmethod
    def clear_correlation_id(cls):
        """Clear correlation ID for current thread"""
        if hasattr(cls, "_thread_correlation_id"):
            delattr(cls, "_thread_correlation_id")


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Add log level
        log_record["level"] = record.levelname
        
        # Add logger name
        log_record["logger"] = record.name
        
        # Add correlation ID
        log_record["correlation_id"] = getattr(record, "correlation_id", "unknown")
        
        # Add service name
        log_record["service"] = getattr(record, "service", "jobswipe")
        
        # Add environment
        log_record["environment"] = getattr(record, "environment", "development")
        
        # Add source location
        log_record["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }
        
        # Remove default fields that are redundant
        if "asctime" in log_record:
            del log_record["asctime"]


class DatadogFormatter(CustomJsonFormatter):
    """JSON formatter optimized for Datadog ingestion"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Datadog-specific fields
        log_record["dd.service"] = log_record.get("service", "jobswipe")
        log_record["dd.env"] = log_record.get("environment", "development")
        log_record["dd.version"] = os.getenv("APP_VERSION", "1.0.0")
        
        # Map standard fields to Datadog format
        log_record["status"] = log_record.get("level", "INFO").lower()
        log_record["message"] = log_record.get("message", "")
        
        # Add trace correlation if available
        trace_id = os.getenv("DD_TRACE_ID")
        span_id = os.getenv("DD_SPAN_ID")
        if trace_id:
            log_record["dd.trace_id"] = trace_id
        if span_id:
            log_record["dd.span_id"] = span_id


class ELKFormatter(CustomJsonFormatter):
    """JSON formatter optimized for ELK stack ingestion"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # ELK-specific fields
        log_record["@timestamp"] = log_record.get("timestamp")
        log_record["@version"] = "1"
        
        # ECS (Elastic Common Schema) fields
        log_record["ecs.version"] = "1.12.0"
        log_record["event.dataset"] = log_record.get("service", "jobswipe")
        log_record["service.name"] = log_record.get("service", "jobswipe")
        log_record["service.environment"] = log_record.get("environment", "development")
        
        # Log level mapping
        log_record["log.level"] = log_record.get("level", "INFO")
        log_record["log.logger"] = log_record.get("logger", "root")


def get_log_level() -> str:
    """Get log level from environment"""
    env = os.getenv("ENVIRONMENT", "development")
    
    # Default log levels per environment
    default_levels = {
        "development": "DEBUG",
        "staging": "INFO",
        "production": "WARNING",
    }
    
    return os.getenv("LOG_LEVEL", default_levels.get(env, "INFO"))


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration based on environment"""
    
    env = os.getenv("ENVIRONMENT", "development")
    log_level = get_log_level()
    log_format = os.getenv("LOG_FORMAT", "json")  # json, text, datadog, elk
    
    # Base configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "correlation_id": {
                "()": CorrelationIdFilter,
            }
        },
        "formatters": {
            "json": {
                "()": CustomJsonFormatter,
                "fmt": "%(timestamp)s %(level)s %(name)s %(message)s",
            },
            "datadog": {
                "()": DatadogFormatter,
                "fmt": "%(timestamp)s %(level)s %(name)s %(message)s",
            },
            "elk": {
                "()": ELKFormatter,
                "fmt": "%(timestamp)s %(level)s %(name)s %(message)s",
            },
            "text": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "security": {
                "()": CustomJsonFormatter,
                "fmt": "%(timestamp)s SECURITY %(level)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": log_format if log_format in ["json", "datadog", "elk"] else "text",
                "stream": "ext://sys.stdout",
                "filters": ["correlation_id"],
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": log_format if log_format in ["json", "datadog", "elk"] else "text",
                "filename": os.getenv("LOG_FILE", "logs/app.log"),
                "maxBytes": int(os.getenv("LOG_MAX_SIZE", "10485760")),  # 10MB
                "backupCount": int(os.getenv("LOG_BACKUP_COUNT", "5")),
                "filters": ["correlation_id"],
            },
            "security_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "security",
                "filename": "logs/security.log",
                "maxBytes": int(os.getenv("LOG_MAX_SIZE", "10485760")),
                "backupCount": int(os.getenv("LOG_BACKUP_COUNT", "5")),
                "filters": ["correlation_id"],
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": log_format if log_format in ["json", "datadog", "elk"] else "text",
                "filename": "logs/error.log",
                "maxBytes": int(os.getenv("LOG_MAX_SIZE", "10485760")),
                "backupCount": int(os.getenv("LOG_BACKUP_COUNT", "5")),
                "filters": ["correlation_id"],
            },
        },
        "loggers": {
            # Root logger
            "": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            # API logger
            "api": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            # Worker logger
            "workers": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            # Service logger
            "services": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            # Database logger
            "db": {
                "handlers": ["console", "file"],
                "level": "WARNING" if env == "production" else log_level,
                "propagate": False,
            },
            # Security logger
            "security": {
                "handlers": ["security_file", "console"],
                "level": "INFO",
                "propagate": False,
            },
            # Error logger
            "error": {
                "handlers": ["error_file", "console"],
                "level": "ERROR",
                "propagate": False,
            },
            # Third-party loggers
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "celery": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "sqlalchemy": {
                "handlers": ["console"],
                "level": "WARNING" if env == "production" else "INFO",
                "propagate": False,
            },
        },
    }
    
    # Add ELK-specific handlers if enabled
    if os.getenv("ELK_ENABLED", "false").lower() == "true":
        config["handlers"]["logstash"] = {
            "class": "logging.handlers.SocketHandler",
            "host": os.getenv("LOGSTASH_HOST", "localhost"),
            "port": int(os.getenv("LOGSTASH_PORT", "5044")),
            "formatter": "elk",
            "filters": ["correlation_id"],
        }
        
        # Add logstash handler to all loggers
        for logger_name in config["loggers"]:
            if "logstash" not in config["loggers"][logger_name]["handlers"]:
                config["loggers"][logger_name]["handlers"].append("logstash")
    
    # Add Datadog-specific handlers if enabled
    if os.getenv("DATADOG_ENABLED", "false").lower() == "true":
        config["handlers"]["datadog"] = {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "datadog",
            "stream": "ext://sys.stdout",
            "filters": ["correlation_id"],
        }
        
        # Use datadog formatter for console in production
        if env == "production":
            config["handlers"]["console"]["formatter"] = "datadog"
    
    return config


def setup_logging():
    """Setup logging configuration"""
    # Ensure log directory exists
    log_file = os.getenv("LOG_FILE", "logs/app.log")
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Ensure security log directory exists
    security_log_dir = os.path.dirname("logs/security.log")
    if security_log_dir and not os.path.exists(security_log_dir):
        os.makedirs(security_log_dir, exist_ok=True)
    
    # Ensure error log directory exists
    error_log_dir = os.path.dirname("logs/error.log")
    if error_log_dir and not os.path.exists(error_log_dir):
        os.makedirs(error_log_dir, exist_ok=True)
    
    # Apply configuration
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Log startup
    logger = logging.getLogger("api")
    logger.info(
        "Logging configured",
        extra={
            "environment": os.getenv("ENVIRONMENT", "development"),
            "log_level": get_log_level(),
            "log_format": os.getenv("LOG_FORMAT", "json"),
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)


def get_correlation_id() -> str:
    """Get current correlation ID or generate new one"""
    correlation_id = CorrelationIdFilter.get_correlation_id()
    if correlation_id == "unknown":
        correlation_id = str(uuid.uuid4())
        CorrelationIdFilter.set_correlation_id(correlation_id)
    return correlation_id


def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context"""
    CorrelationIdFilter.set_correlation_id(correlation_id)


def clear_correlation_id():
    """Clear correlation ID for current context"""
    CorrelationIdFilter.clear_correlation_id()


class LogContext:
    """Context manager for correlation ID"""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.previous_id = None
    
    def __enter__(self):
        self.previous_id = CorrelationIdFilter.get_correlation_id()
        CorrelationIdFilter.set_correlation_id(self.correlation_id)
        return self.correlation_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_id != "unknown":
            CorrelationIdFilter.set_correlation_id(self.previous_id)
        else:
            CorrelationIdFilter.clear_correlation_id()


# Convenience functions for structured logging
def log_info(logger: logging.Logger, message: str, extra: Optional[Dict[str, Any]] = None):
    """Log info message with structured data"""
    logger.info(message, extra=extra or {})


def log_warning(logger: logging.Logger, message: str, extra: Optional[Dict[str, Any]] = None):
    """Log warning message with structured data"""
    logger.warning(message, extra=extra or {})


def log_error(logger: logging.Logger, message: str, extra: Optional[Dict[str, Any]] = None):
    """Log error message with structured data"""
    logger.error(message, extra=extra or {})


def log_debug(logger: logging.Logger, message: str, extra: Optional[Dict[str, Any]] = None):
    """Log debug message with structured data"""
    logger.debug(message, extra=extra or {})


def log_security(event: str, extra: Optional[Dict[str, Any]] = None):
    """Log security event"""
    logger = logging.getLogger("security")
    logger.info(event, extra=extra or {})


# Initialize logging on module import
setup_logging()
