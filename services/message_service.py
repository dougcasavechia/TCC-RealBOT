import os
from datetime import datetime
import requests
from config import BASE_URL, CONVERSATIONS_DIR
from logger import logger  # Usando o módulo de logs

def enviar_mensagem(contato, mensagem):
    """
    Envia uma mensagem para o número informado via WPPConnect.
    """
    url = f"{BASE_URL}/whatsapp-session/sendText"
    payload = {"phone": contato, "message": mensagem}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Levanta um erro se a resposta não for 200 OK
        logger.info(f"✅ Mensagem enviada para {contato}: {mensagem}")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro ao enviar mensagem para {contato}: {e}")

def salvar_mensagem_em_arquivo(contato, nome_cliente, mensagem):
    """
    Salva as mensagens em um arquivo de texto para registro.
    """
    try:
        hoje = datetime.now().strftime("%Y-%m-%d")
        nome_arquivo = os.path.join(CONVERSATIONS_DIR, f"{hoje}_user_{contato}.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(nome_arquivo, "a", encoding="utf-8") as arquivo:
            arquivo.write(f"[{timestamp}] [Cliente: {nome_cliente}] {mensagem}\n")
        
        logger.info(f"💾 Mensagem registrada para {contato}")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar mensagem no arquivo para {contato}: {e}")

