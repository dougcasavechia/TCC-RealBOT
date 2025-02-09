from flask import Flask
from threading import Thread, enumerate  # Importação correta
from routes import webhook_bp
from services.state_service import monitor_inactivity
from logger import logger

app = Flask(__name__)
app.register_blueprint(webhook_bp)

def start_monitoring():
    """Inicia o monitoramento de inatividade em uma thread separada."""
    if not any(isinstance(t, Thread) and t.name == "MonitorThread" for t in enumerate()):
        Thread(target=monitor_inactivity, daemon=True, name="MonitorThread").start()

if __name__ == "__main__":
    logger.info("🚀 Bot iniciado. Aguardando mensagens...")
    start_monitoring()
    app.run(port=5000, debug=False)
