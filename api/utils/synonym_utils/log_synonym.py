
import logging
import os

LOG_FILE_PATH = 'auto_synonyms.log'

# Set up a dedicated logger for synonym generation
logger = logging.getLogger('auto_synonyms')
logger.setLevel(logging.INFO)

# Create a file handler if one doesn't exist yet
if not logger.handlers:
    # Ensure the directory exists
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    handler = logging.FileHandler(LOG_FILE_PATH)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def log_synonym(log_type, message, synonym_data=None):
    """
    Logs information about the synonym generation process.
    """
    log_message = f"[{log_type.upper()}] {message}"
    if synonym_data:
        log_message += f" | Data: {synonym_data}"
    
    logger.info(log_message)

