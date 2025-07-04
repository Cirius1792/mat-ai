"""Centralized logging configuration for PMAI."""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    service_name: str = "pmai"
) -> None:
    """Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, logs to stderr only
        service_name: Name of the service for log identification
        
    The logging format includes:
        - Timestamp in ISO format with milliseconds
        - Log level
        - Service name
        - Module name
        - Function name
        - Line number
        - Message
    """
    log_format = (
        "%(asctime)s.%(msecs)03d|%(levelname)s|%(service_name)s|"
        "%(module)s:%(funcName)s:%(lineno)d|%(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    # Create formatter
    formatter = logging.Formatter(
        log_format,
        date_format
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # logging.getLogger('pmai').setLevel(log_level)

    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Add custom context
    class ServiceNameFilter(logging.Filter):
        def __init__(self, service_name: str):
            super().__init__()
            self.service_name = service_name

        def filter(self, record: logging.LogRecord) -> bool:
            record.service_name = self.service_name  # type: ignore
            return True

    service_name_filter = ServiceNameFilter(service_name)

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(service_name_filter)
    root_logger.addHandler(console_handler)

    # File handler if log_file specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10_485_760,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(service_name_filter)
        root_logger.addHandler(file_handler)

    # Suppress overly verbose logging from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

