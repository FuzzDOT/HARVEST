"""
Logging Configuration
Centralized logging setup for the HARVEST application.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path

from app.config import settings


def setup_logger(name: str = None) -> logging.Logger:
    """
    Set up and configure logger with appropriate handlers and formatters.
    
    Args:
        name: Logger name (usually __name__ from calling module)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name or "harvest")
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    simple_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log file path is configured)
    if hasattr(settings, 'LOG_FILE') and settings.LOG_FILE:
        try:
            # Create log directory if it doesn't exist
            log_file_path = Path(settings.LOG_FILE)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                filename=settings.LOG_FILE,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            logger.warning(f"Could not set up file logging: {e}")
    
    # Error file handler for ERROR and CRITICAL levels
    try:
        error_log_path = Path("logs/error.log")
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        error_handler = logging.handlers.RotatingFileHandler(
            filename="logs/error.log",
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
        
    except Exception as e:
        logger.warning(f"Could not set up error file logging: {e}")
    
    return logger


def log_request(request_method: str, request_url: str, response_status: int, 
                response_time: float = None, user_id: int = None):
    """
    Log HTTP request information.
    
    Args:
        request_method: HTTP method (GET, POST, etc.)
        request_url: Request URL
        response_status: HTTP response status code
        response_time: Request processing time in seconds
        user_id: User ID if authenticated
    """
    logger = logging.getLogger("harvest.requests")
    
    extra_info = []
    if user_id:
        extra_info.append(f"user_id={user_id}")
    if response_time:
        extra_info.append(f"time={response_time:.3f}s")
    
    extra_str = f" ({', '.join(extra_info)})" if extra_info else ""
    
    log_message = f"{request_method} {request_url} -> {response_status}{extra_str}"
    
    if response_status >= 500:
        logger.error(log_message)
    elif response_status >= 400:
        logger.warning(log_message)
    else:
        logger.info(log_message)


def log_prediction(prediction_type: str, user_id: int, location: str, 
                  confidence_score: float = None, processing_time: float = None):
    """
    Log ML prediction information.
    
    Args:
        prediction_type: Type of prediction made
        user_id: User who requested prediction
        location: Location for prediction
        confidence_score: Model confidence score
        processing_time: Time taken to process prediction
    """
    logger = logging.getLogger("harvest.predictions")
    
    extra_info = []
    if confidence_score:
        extra_info.append(f"confidence={confidence_score:.3f}")
    if processing_time:
        extra_info.append(f"time={processing_time:.3f}s")
    
    extra_str = f" ({', '.join(extra_info)})" if extra_info else ""
    
    logger.info(f"Prediction: {prediction_type} for user {user_id} at {location}{extra_str}")


def log_alert(alert_type: str, user_id: int, location: str, triggered: bool = False):
    """
    Log alert information.
    
    Args:
        alert_type: Type of alert
        user_id: User who owns the alert
        location: Alert location
        triggered: Whether alert was triggered
    """
    logger = logging.getLogger("harvest.alerts")
    
    action = "TRIGGERED" if triggered else "checked"
    logger.info(f"Alert {action}: {alert_type} for user {user_id} at {location}")


def log_marketplace_activity(activity_type: str, user_id: int, product_id: int = None, 
                           order_id: int = None, amount: float = None):
    """
    Log marketplace activity.
    
    Args:
        activity_type: Type of activity (product_created, order_placed, etc.)
        user_id: User performing the activity
        product_id: Product ID if applicable
        order_id: Order ID if applicable
        amount: Transaction amount if applicable
    """
    logger = logging.getLogger("harvest.marketplace")
    
    extra_info = []
    if product_id:
        extra_info.append(f"product_id={product_id}")
    if order_id:
        extra_info.append(f"order_id={order_id}")
    if amount:
        extra_info.append(f"amount=${amount:.2f}")
    
    extra_str = f" ({', '.join(extra_info)})" if extra_info else ""
    
    logger.info(f"Marketplace: {activity_type} by user {user_id}{extra_str}")


def log_performance(operation: str, duration: float, additional_info: dict = None):
    """
    Log performance metrics.
    
    Args:
        operation: Name of the operation
        duration: Duration in seconds
        additional_info: Additional context information
    """
    logger = logging.getLogger("harvest.performance")
    
    extra_info = []
    if additional_info:
        for key, value in additional_info.items():
            extra_info.append(f"{key}={value}")
    
    extra_str = f" ({', '.join(extra_info)})" if extra_info else ""
    
    level = logging.WARNING if duration > 5.0 else logging.INFO
    logger.log(level, f"Performance: {operation} took {duration:.3f}s{extra_str}")


class PerformanceLogger:
    """Context manager for logging operation performance."""
    
    def __init__(self, operation: str, additional_info: dict = None):
        self.operation = operation
        self.additional_info = additional_info or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            
            if exc_type:
                self.additional_info['error'] = str(exc_val)
                log_performance(f"{self.operation} (FAILED)", duration, self.additional_info)
            else:
                log_performance(self.operation, duration, self.additional_info)


# Configure root logger
setup_logger()