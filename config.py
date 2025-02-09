import os

# Configurações gerais
BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")

# Diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONVERSATIONS_DIR = os.getenv("CONVERSATIONS_DIR", os.path.join(BASE_DIR, "conversations"))
LOG_DIR = os.getenv("LOG_DIR", os.path.join(BASE_DIR, "logs"))
INPUT_DIR = os.getenv("INPUT_DIR", os.path.join(BASE_DIR, "input"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(BASE_DIR, "output"))

# Arquivos
CLIENT_FILE_PATH = os.path.join(INPUT_DIR, "cliente.xlsx")
PROJECT_FILE_PATH = os.path.join(INPUT_DIR, "projetos.xlsx")
MATERIAL_FILE_PATH = os.path.join(INPUT_DIR, "materia_prima.xlsx")

# Configurações de tempo
TIMEOUT_WARNING = int(os.getenv("TIMEOUT_WARNING", "100"))  # Forçar string padrão como fallback
TIMEOUT_FINAL = int(os.getenv("TIMEOUT_FINAL", "100"))

def setup_directories():
    """Cria diretórios necessários para o funcionamento do sistema."""
    for directory in [CONVERSATIONS_DIR, LOG_DIR, INPUT_DIR, OUTPUT_DIR]:
        os.makedirs(directory, exist_ok=True)

if __name__ == "__main__":
    setup_directories()
