from flask import Blueprint, request, jsonify
from services.message_handler import gerenciar_mensagem_recebida
from logger import logger

webhook_bp = Blueprint("webhook", __name__)

@webhook_bp.route("/webhook", methods=["POST"])
def webhook():
    try:
        if not request.is_json:
            logger.warning("❌ Requisição inválida (não é JSON).")
            return jsonify({"status": "error", "message": "Requisição inválida, esperado JSON"}), 400

        data = request.get_json()
        contato = data.get("from", "").split("@")[0] if "from" in data else None
        texto = data.get("body", "").strip() if "body" in data else None

        if not contato or not texto:
            logger.warning("❌ Dados insuficientes no payload.")
            return jsonify({"status": "error", "message": "Dados insuficientes no payload"}), 400

        logger.info(f"📩 Webhook ativado - Contato: {contato}, Mensagem: {texto}")
        
        gerenciar_mensagem_recebida(contato, texto)

        logger.info(f"✅ Mensagem processada com sucesso para {contato}.")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"❌ Erro no webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Erro interno no servidor"}), 500

