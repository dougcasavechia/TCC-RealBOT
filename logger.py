import logging
import os
from config import LOG_DIR

LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_logger(level=logging.INFO):
    """Configura o logger da aplicação."""
    os.makedirs(LOG_DIR, exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("AppLogger")

logger = setup_logger(level=os.getenv("LOG_LEVEL", "INFO").upper())

