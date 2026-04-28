import logging
import logging.handlers
import os
import sys

def setup_logging():
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    
    # Create logs directory if it doesn't exist (just in case)
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "app.log")
    
    # Create the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 1. Console Handler (for Docker logs / stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 2. Rotating File Handler (rolling window)
    # 5MB per file, max 5 backup files
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    logging.info(f"Logging initialized. Level: {log_level}")
