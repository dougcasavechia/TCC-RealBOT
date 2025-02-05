import os

# Configurações gerais
BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")

# Diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONVERSATIONS_DIR = os.getenv("CONVERSATIONS_DIR", os.path.join(BASE_DIR, "conversations"))
LOG_DIR = os.getenv("LOG_DIR", os.path.join(BASE_DIR, "logs"))
INPUT_DIR = os.getenv("INPUT_DIR", os.path.join(BASE_DIR, "input"))

# Arquivos
CLIENT_FILE_PATH = os.path.join(INPUT_DIR, "cliente.xlsx")
PROJECT_FILE_PATH = os.path.join(INPUT_DIR, "projetos.xlsx")
TABLE_FILE_PATH = os.path.join(INPUT_DIR, "nova_tabela.xlsx")

# Configurações de tempo
TIMEOUT_WARNING = int(os.getenv("TIMEOUT_WARNING", 10))
TIMEOUT_FINAL = int(os.getenv("TIMEOUT_FINAL", 10))

def setup_directories():
    """Cria diretórios necessários para o funcionamento do sistema."""
    for directory in [CONVERSATIONS_DIR, LOG_DIR, INPUT_DIR]:
        os.makedirs(directory, exist_ok=True)

setup_directories()

