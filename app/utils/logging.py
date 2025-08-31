import logging
import os
from pythonjsonlogger import jsonlogger

def configure_json_logging(level: int = logging.INFO) -> None:
    """Configure JSON logging for the application."""
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers[:] = []
    
    # Create handler
    handler = logging.StreamHandler()
    
    # Create formatter with correlation ID support
    fmt = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d %(funcName)s"
    )
    handler.setFormatter(fmt)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Set specific loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
