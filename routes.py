from flask import Blueprint, request, jsonify
from services.message_handler import gerenciar_mensagem_recebida

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

        print(f"[DEBUG] Mensagem recebida de {contato}: {texto}")

        # Processar a mensagem recebida
        gerenciar_mensagem_recebida(contato, texto)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"[ERROR] Erro no webhook: {e}")
        return jsonify({"status": "error", "message": "Erro interno no servidor"}), 500

