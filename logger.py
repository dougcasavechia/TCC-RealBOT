import logging
import os
from config import LOG_DIR

LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_logger():
    """Configura o logger da aplicação sem criar múltiplos handlers."""
    if not logging.getLogger("AppLogger").handlers:
        os.makedirs(LOG_DIR, exist_ok=True)

        logger = logging.getLogger("AppLogger")
        logger.setLevel(logging.getLevelName(os.getenv("LOG_LEVEL", "INFO").upper()))

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logging.getLogger("AppLogger")

logger = setup_logger()
