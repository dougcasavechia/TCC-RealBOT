import logging
import os

# Diretório para armazenar logs
LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configuração do logger
LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_logger():
    """Configura o logger para a aplicação"""
    logging.basicConfig(
        level=logging.INFO,  # Pode ser DEBUG para mais detalhes
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()  # Exibe logs no console
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()

