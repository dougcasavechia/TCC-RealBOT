import os

# Configurações gerais
BASE_URL = "http://localhost:3000"

# Diretórios
CLIENT_FILE_PATH = r"C:\Users\dougl\OneDrive\Área de Trabalho\python-whatsapp\input\cliente.xlsx"
PRODUCT_FILE_PATH = r"C:\Users\dougl\OneDrive\Área de Trabalho\python-whatsapp\input\tipo_produto.xlsx"
PROJECT_FILE_PATH = r"C:\Users\dougl\OneDrive\Área de Trabalho\python-whatsapp\input\projetos.xlsx"
CONVERSATIONS_DIR = "conversations"

# Configurações de tempo
TIMEOUT_WARNING = 60  # Tempo em segundos antes do aviso de inatividade
TIMEOUT_FINAL = 60    # Tempo adicional antes de encerrar a conversa

# Criação do diretório para salvar mensagens (se não existir)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
