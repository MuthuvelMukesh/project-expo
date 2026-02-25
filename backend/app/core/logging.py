"""
Structured logging configuration for CampusIQ
"""

import logging
import logging.config
import json
import sys
from datetime import datetime
from typing import Optional
from pythonjsonlogger import jsonlogger


class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module


def configure_logging(env: str = "development", log_level: str = "INFO"):
    """Configure structured logging for the application."""

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
            },
            "detailed": {
                "format": "[%(asctime)s] %(name)s:%(lineno)d - %(levelname)s - %(message)s"
            },
            "json": {
                "()": StructuredFormatter,
                "format": "%(timestamp)s %(level)s %(name)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "json" if env == "production" else "detailed",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "json",
                "filename": "logs/campusiq.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/campusiq_errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "campusiq": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "app": {
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file"],
        },
    }

    logging.config.dictConfig(config)
    return logging.getLogger("campusiq")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(f"campusiq.{name}")


# Middleware for request/response logging
class LoggingMiddleware:
    """ASGI middleware for logging HTTP requests and responses."""

    def __init__(self, app, logger: Optional[logging.Logger] = None):
        self.app = app
        self.logger = logger or get_logger("api")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_method = scope["method"]
        request_path = scope["path"]
        request_id = str(scope.get("query_string", ""))

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                self.logger.info(
                    f"{request_method} {request_path}",
                    extra={
                        "status_code": status_code,
                        "request_id": request_id,
                        "path": request_path,
                        "method": request_method,
                    },
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)
