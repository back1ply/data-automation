import logging
from coloredlogs import ColoredFormatter
import os

def init_logger(directory):
    # Initialize the logger
    logger: logging.Logger = None

    # Check if the 'logs' directory exists, and create it if it doesn't
    logs_dir = os.path.join(directory, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, 'process_log.log')

    # Setup logger configuration
    LOG_FORMAT = '[%(asctime)s] [%(name)s] [%(funcName)s:%(lineno)d] %(levelname)s: %(message)s'
    LOG_DATE_FORMAT = '%I:%M:%S'
    LOG_LEVEL = logging.INFO
    LOG_FILE_PATH = os.path.join(logs_dir, 'process_log.log')

    # Get the logger
    logger = logging.getLogger("functions")

    # Check if handlers are already added to avoid duplication
    if not logger.hasHandlers():
        logger.setLevel(LOG_LEVEL)

        # Create a colored formatter for the console
        console_formatter = ColoredFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        # Create a regular non-colored formatter for the log file
        file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

        # Create a handler for console logging
        stream = logging.StreamHandler()
        stream.setLevel(LOG_LEVEL)
        stream.setFormatter(console_formatter)

        # Create a handler for file logging
        file_handler = logging.FileHandler(LOG_FILE_PATH)
        file_handler.setFormatter(file_formatter)

        # Add handlers to the logger
        logger.addHandler(stream)
        logger.addHandler(file_handler)

    return logger