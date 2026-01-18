"""
Structured Logging Configuration for Data Desensitization Platform

This module configures structlog for structured logging with JSON output,
providing consistent log formatting across the application.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.types import EventDict, Processor


def add_app_context(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application context to log entries.
    
    Args:
        logger: The logger instance
        method_name: The logging method name
        event_dict: The event dictionary
        
    Returns:
        Modified event dictionary with app context
    """
    event_dict["app"] = "desensitization-platform"
    event_dict["environment"] = "production"  # Can be configured via env var
    return event_dict


def censor_sensitive_data(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Censor sensitive data in log entries.
    
    Removes or masks sensitive fields like passwords, tokens, etc.
    
    Args:
        logger: The logger instance
        method_name: The logging method name
        event_dict: The event dictionary
        
    Returns:
        Modified event dictionary with censored data
    """
    sensitive_keys = {"password", "token", "secret", "api_key", "auth"}
    
    for key in list(event_dict.keys()):
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            event_dict[key] = "***CENSORED***"
    
    return event_dict


def configure_logging(log_level: str = "INFO", json_logs: bool = True) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output logs in JSON format (True for production)
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )
    
    # Define processors for structlog
    processors: list[Processor] = [
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add application context
        add_app_context,
        # Censor sensitive data
        censor_sensitive_data,
        # Add stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.processors.format_exc_info,
        # Decode unicode
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add appropriate renderer based on output format
    if json_logs:
        # JSON output for production (machine-readable)
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Console output for development (human-readable)
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# Logging helper functions for common operations
class LogHelper:
    """Helper class for common logging operations"""
    
    @staticmethod
    def log_request(logger: structlog.stdlib.BoundLogger, method: str, path: str, **kwargs: Any) -> None:
        """
        Log an HTTP request.
        
        Args:
            logger: Logger instance
            method: HTTP method
            path: Request path
            **kwargs: Additional context
        """
        logger.info(
            "http_request",
            method=method,
            path=path,
            **kwargs
        )
    
    @staticmethod
    def log_response(
        logger: structlog.stdlib.BoundLogger, 
        method: str, 
        path: str, 
        status_code: int,
        duration_ms: float = None,
        **kwargs: Any
    ) -> None:
        """
        Log an HTTP response.
        
        Args:
            logger: Logger instance
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            **kwargs: Additional context
        """
        log_data = {
            "method": method,
            "path": path,
            "status_code": status_code,
            **kwargs
        }
        
        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms
        
        if status_code >= 500:
            logger.error("http_response", **log_data)
        elif status_code >= 400:
            logger.warning("http_response", **log_data)
        else:
            logger.info("http_response", **log_data)
    
    @staticmethod
    def log_database_operation(
        logger: structlog.stdlib.BoundLogger,
        operation: str,
        table: str,
        success: bool = True,
        **kwargs: Any
    ) -> None:
        """
        Log a database operation.
        
        Args:
            logger: Logger instance
            operation: Operation type (insert, update, delete, select)
            table: Table name
            success: Whether operation succeeded
            **kwargs: Additional context
        """
        if success:
            logger.info(
                "database_operation",
                operation=operation,
                table=table,
                success=success,
                **kwargs
            )
        else:
            logger.error(
                "database_operation",
                operation=operation,
                table=table,
                success=success,
                **kwargs
            )
    
    @staticmethod
    def log_file_operation(
        logger: structlog.stdlib.BoundLogger,
        operation: str,
        filename: str,
        file_size: int = None,
        **kwargs: Any
    ) -> None:
        """
        Log a file operation.
        
        Args:
            logger: Logger instance
            operation: Operation type (upload, parse, export)
            filename: File name
            file_size: File size in bytes
            **kwargs: Additional context
        """
        log_data = {
            "operation": operation,
            "filename": filename,
            **kwargs
        }
        
        if file_size is not None:
            log_data["file_size"] = file_size
        
        logger.info("file_operation", **log_data)
    
    @staticmethod
    def log_processing_operation(
        logger: structlog.stdlib.BoundLogger,
        operation: str,
        duration_ms: float = None,
        items_processed: int = None,
        **kwargs: Any
    ) -> None:
        """
        Log a processing operation (recognition, desensitization).
        
        Args:
            logger: Logger instance
            operation: Operation type
            duration_ms: Processing duration in milliseconds
            items_processed: Number of items processed
            **kwargs: Additional context
        """
        log_data = {
            "operation": operation,
            **kwargs
        }
        
        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms
        
        if items_processed is not None:
            log_data["items_processed"] = items_processed
        
        logger.info("processing_operation", **log_data)
    
    @staticmethod
    def log_error(
        logger: structlog.stdlib.BoundLogger,
        error_type: str,
        error_message: str,
        error_code: str = None,
        **kwargs: Any
    ) -> None:
        """
        Log an error with structured information.
        
        Args:
            logger: Logger instance
            error_type: Type of error
            error_message: Error message
            error_code: Error code
            **kwargs: Additional context
        """
        log_data = {
            "error_type": error_type,
            "error_message": error_message,
            **kwargs
        }
        
        if error_code:
            log_data["error_code"] = error_code
        
        logger.error("application_error", **log_data)
