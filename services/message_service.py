import os
import requests
from datetime import datetime
from config import BASE_URL, CONVERSATIONS_DIR
from logger import logger  # Usando o módulo de logs
import time

def enviar_mensagem(contato, mensagem, tentativas=3, intervalo=2):
    # 🚫 Bloqueia envio caso o contato seja "status"
    if contato.lower() == "status":
        logger.warning("🚫 Tentativa de envio de mensagem para 'status' bloqueada.")
        return False

    url = f"{BASE_URL}/whatsapp-session/sendText"
    payload = {"phone": contato, "message": mensagem}

    for tentativa in range(tentativas):
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"✅ Mensagem enviada para {contato}: {mensagem}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao enviar mensagem (tentativa {tentativa+1}/{tentativas}): {e}")
            time.sleep(intervalo)  # Espera antes de tentar novamente
    return False


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

