import os
from datetime import datetime
import requests
from config import BASE_URL, CONVERSATIONS_DIR

def enviar_mensagem(contato, mensagem):
    """
    Envia uma mensagem para o número informado via WPPConnect.
    """
    url = f"{BASE_URL}/whatsapp-session/sendText"
    payload = {"phone": contato, "message": mensagem} 
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"Mensagem enviada para {contato}: {mensagem}")
        else:
            print(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erro de conexão ao enviar mensagem: {e}")

def salvar_mensagem_em_arquivo(contato, nome_cliente, mensagem):
    """
    Salva as mensagens em um arquivo de texto para registro.
    """
    hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = os.path.join(CONVERSATIONS_DIR, f"{hoje}_user_{contato}.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(nome_arquivo, "a", encoding="utf-8") as arquivo:
        arquivo.write(f"[{timestamp}] [Cliente: {nome_cliente}] {mensagem}\n")
