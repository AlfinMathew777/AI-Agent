"""
Structured logging configuration for the hotel management system.

This module provides:
- JSON formatted logs for easy parsing
- Contextual logging with tenant_id, user_id, etc.
- Log rotation to prevent disk space issues
- Different log levels for different environments
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import os


class JSONFormatter(logging.Formatter):
    """
    Format logs as JSON for easy parsing and analysis.
    
    Output example:
    {
        "timestamp": "2026-02-04T12:00:00Z",
        "level": "ERROR",
        "module": "properties",
        "function": "pause_property",
        "message": "Property not found",
        "tenant_id": "southern_horizons",
        "extra": {...}
    }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        # Add contextual information if available
        for field in ["tenant_id", "user_id", "session_id", "request_id"]:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        # Add any extra fields
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    """
    Format logs in human-readable format for console output.
    
    Output example:
    2026-02-04 12:00:00 | ERROR | properties.pause_property:42 | Property not found
    """
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        location = f"{record.module}.{record.funcName}:{record.lineno}"
        
        msg = f"{timestamp} | {record.levelname:8} | {location:40} | {record.getMessage()}"
        
        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)
        
        return msg


def setup_logging(
    app_name: str = "hotel_app",
    log_level: str = "INFO",
    log_dir: str = "logs",
    environment: str = "development"
) -> logging.Logger:
    """
    Configure logging for the entire application.
    
    Args:
        app_name: Name of the application (used in log filenames)
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        environment: Environment name (development, staging, production)
    
    Returns:
        Configured logger instance
    """
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # ========================================================================
    # File Handler - JSON format for parsing
    # ========================================================================
    
    json_file = log_path / f"{app_name}.json"
    file_handler = RotatingFileHandler(
        json_file,
        maxBytes=10 * 1024 * 1024,  # 10MB per file
        backupCount=5,  # Keep 5 backup files
        encoding='utf-8'
    )
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    # ========================================================================
    # Console Handler - Human readable format
    # ========================================================================
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(HumanReadableFormatter())
    
    # Only show DEBUG logs in console for development
    if environment == "development":
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.WARNING)
    
    logger.addHandler(console_handler)
    
    # ========================================================================
    # Error File Handler - Separate file for errors only
    # ========================================================================
    
    error_file = log_path / f"{app_name}_errors.log"
    error_handler = RotatingFileHandler(
        error_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=10,  # Keep more error logs
        encoding='utf-8'
    )
    error_handler.setFormatter(JSONFormatter())
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)
    
    # Log startup
    logger.info(
        f"Logging initialized for {app_name}",
        extra={
            "log_level": log_level,
            "environment": environment,
            "log_dir": str(log_path.absolute())
        }
    )
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Something happened", extra={"user_id": "123"})
    """
    return logging.getLogger(name)


# ============================================================================
# Contextual Logging Helpers
# ============================================================================

class LogContext:
    """
    Context manager for adding contextual information to logs.
    
    Usage:
        with LogContext(tenant_id="southern_horizons", user_id="admin"):
            logger.info("User logged in")
            # This log will include tenant_id and user_id
    """
    
    def __init__(self, **context):
        self.context = context
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, *args):
        logging.setLogRecordFactory(self.old_factory)
