import logging
import sys
from logging.handlers import RotatingFileHandler
from config.settings import LOG_LEVEL, LOG_FILE

# Formatter schema: [TIMESTAMP] [LEVEL] [MODULE] message
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(name: str) -> logging.Logger:
    """Configures centralized logger per Section 7 specs."""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers on subsequent calls
    if not logger.handlers:
        level_val = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level_val)
        logger.propagate = False
        
        formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level_val)
        logger.addHandler(console_handler)

        # Rotating File Handler (10MB x 5 backups)
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level_val)
        logger.addHandler(file_handler)

    return logger
