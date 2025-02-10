import os
from dotenv import load_dotenv
import logging

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configura o logger
log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("config.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ConfigLogger")

# Configurações gerais
BASE_URL = os.getenv("BASE_URL")

# Diretórios (fixos no código)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONVERSATIONS_DIR = os.path.join(BASE_DIR, "conversations")
LOG_DIR = os.path.join(BASE_DIR, "logs")
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Arquivos
CLIENT_FILE_PATH = os.path.join(INPUT_DIR, "cliente.xlsx")
PROJECT_FILE_PATH = os.path.join(INPUT_DIR, "projetos.xlsx")
MATERIAL_FILE_PATH = os.path.join(INPUT_DIR, "materia_prima.xlsx")

# Configurações de tempo (fixas no código)
TIMEOUT_WARNING = 5
TIMEOUT_FINAL = 10

# Função para criar os diretórios necessários
def setup_directories():
    """Cria diretórios necessários para o funcionamento do sistema."""
    for directory in [CONVERSATIONS_DIR, LOG_DIR, INPUT_DIR, OUTPUT_DIR]:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"📂 Diretório criado/verificado: {directory}")
        except Exception as e:
            logger.error(f"❌ Erro ao criar diretório {directory}: {e}")

if __name__ == "__main__":
    setup_directories()
