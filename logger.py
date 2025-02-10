import logging
import os
from config import LOG_DIR

# Certifica-se de que o diretório de logs existe antes de configurar o logger
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_logger():
    """Configura o logger da aplicação."""
    logger = logging.getLogger("AppLogger")

    if not logger.hasHandlers():  # Evita múltiplos handlers
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, log_level, logging.INFO)  # Garante um nível válido

        logger.setLevel(log_level)

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger

# Instância global do logger
logger = setup_logger()
