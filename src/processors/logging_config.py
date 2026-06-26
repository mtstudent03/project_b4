import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(log_dir="../logs"):
    """
    Configure structured logging with file handlers, rotation, and console output.
    Logs are written to separate files for pipeline activity and authentication events.
    """
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG)
    
    auth_logger = logging.getLogger("auth")
    auth_logger.setLevel(logging.DEBUG)
    
    db_logger = logging.getLogger("db")
    db_logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    app_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "pipeline.log"),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    app_handler.setLevel(logging.DEBUG)
    app_handler.setFormatter(formatter)
    app_logger.addHandler(app_handler)
    
    auth_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "authentication.log"),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    auth_handler.setLevel(logging.DEBUG)
    auth_handler.setFormatter(formatter)
    auth_logger.addHandler(auth_handler)
    
    db_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "database.log"),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    db_handler.setLevel(logging.DEBUG)
    db_handler.setFormatter(formatter)
    db_logger.addHandler(db_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)
    
    return app_logger, auth_logger, db_logger

def get_loggers():
    """Retrieve configured loggers."""
    return (
        logging.getLogger("app"),
        logging.getLogger("auth"),
        logging.getLogger("db")
    )
