from flask import Flask
from threading import Thread
from routes import webhook_bp
from services.state_service import monitor_inactivity

app = Flask(__name__)
app.register_blueprint(webhook_bp)

if __name__ == "__main__":
    print("Bot iniciado. Aguardando mensagens...")
    Thread(target=monitor_inactivity, daemon=True).start()
    app.run(port=5000)
