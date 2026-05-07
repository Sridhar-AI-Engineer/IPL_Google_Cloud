"""Structured logging and monitoring utilities."""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data, default=str)


def setup_logging() -> logging.Logger:
    """Configure structured logging."""
    # Create logs directory
    log_dir = Path(settings.log_file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("ipl-agentic-coach")
    logger.setLevel(getattr(logging, settings.log_level))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Choose formatter
    if settings.log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(settings.log_file_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# Global logger instance
logger = setup_logging()


class MetricsCollector:
    """Collect application metrics."""

    def __init__(self):
        self.metrics: dict[str, Any] = {
            "requests_total": 0,
            "requests_by_status": {},
            "requests_by_endpoint": {},
            "response_times": [],
            "errors": 0,
            "decisions_submitted": 0,
            "users_created": 0,
        }

    def record_request(self, path: str, status_code: int, duration_ms: float):
        """Record HTTP request metrics."""
        self.metrics["requests_total"] += 1
        self.metrics["requests_by_status"][status_code] = (
            self.metrics["requests_by_status"].get(status_code, 0) + 1
        )
        self.metrics["requests_by_endpoint"][path] = (
            self.metrics["requests_by_endpoint"].get(path, 0) + 1
        )
        self.metrics["response_times"].append(duration_ms)
        
        if status_code >= 400:
            self.metrics["errors"] += 1

    def record_decision(self):
        """Record decision submission."""
        self.metrics["decisions_submitted"] += 1

    def record_user_created(self):
        """Record user creation."""
        self.metrics["users_created"] += 1

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics."""
        response_times = self.metrics["response_times"]
        return {
            **self.metrics,
            "avg_response_time_ms": (
                sum(response_times) / len(response_times)
                if response_times else 0
            ),
            "max_response_time_ms": max(response_times) if response_times else 0,
            "min_response_time_ms": min(response_times) if response_times else 0,
        }

    def reset(self):
        """Reset metrics."""
        self.metrics = {
            "requests_total": 0,
            "requests_by_status": {},
            "requests_by_endpoint": {},
            "response_times": [],
            "errors": 0,
            "decisions_submitted": 0,
            "users_created": 0,
        }


# Global metrics collector
metrics = MetricsCollector()
