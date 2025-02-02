from flask import Blueprint, request, jsonify
from services.message_handler import gerenciar_mensagem_recebida
from logger import logger  # Usando o logger centralizado

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Extrair dados do payload
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Payload ausente"}), 400

        contato = data.get('from', '').split('@')[0]
        texto = data.get('body', '').strip()

        if not contato or not texto:
            return jsonify({"status": "error", "message": "Dados insuficientes no payload"}), 400

        logger.debug(f"Mensagem recebida de {contato}: {texto}")

        # Processar a mensagem recebida
        gerenciar_mensagem_recebida(contato, texto)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"Erro no webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Erro interno no servidor"}), 500

