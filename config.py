import os

# Configurações gerais
BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")

# Diretórios
CLIENT_FILE_PATH = os.getenv("CLIENT_FILE_PATH", r"input/cliente.xlsx")
PRODUCT_FILE_PATH = os.getenv("PRODUCT_FILE_PATH", r"input/tipo_produto.xlsx")
PROJECT_FILE_PATH = os.getenv("PROJECT_FILE_PATH", r"input/projetos.xlsx")
CONVERSATIONS_DIR = os.getenv("CONVERSATIONS_DIR", "conversations")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Obtém o diretório do script
CLIENT_FILE_PATH = os.path.join(BASE_DIR, "input", "cliente.xlsx")

print(f"Caminho absoluto do arquivo: {CLIENT_FILE_PATH}")
print(f"Existe? {os.path.exists(CLIENT_FILE_PATH)}")


# Configurações de tempo
TIMEOUT_WARNING = int(os.getenv("TIMEOUT_WARNING", 10))  # Segundos antes do aviso de inatividade
TIMEOUT_FINAL = int(os.getenv("TIMEOUT_FINAL", 10))  # Tempo adicional antes de encerrar a conversa

# Criação do diretório para salvar mensagens (se não existir)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)

