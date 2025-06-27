from flask import Flask, request, jsonify
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

# Conexão com o MongoDB
uri = os.getenv("MONGO_URI")
client = MongoClient(uri, server_api=ServerApi("1"))
db = client["usuarios"]
colecao = db["usuarios_autorizados"]

# Criar app Flask
app = Flask(__name__)

@app.route("/kiwify", methods=["POST"])
def receber_webhook():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Payload inválido ou vazio"}), 400

    # Log no console (opcional)
    print("📩 Webhook recebido:", data)

    # Extrair dados principais com fallback em caso de ausência
    email = data.get("customer_email")
    status = data.get("status", "indefinido")
    subscription_status = data.get("subscription_status", "indefinido")

    if not email:
        return jsonify({"error": "E-mail não encontrado no payload"}), 400

    # Salvar ou atualizar no banco
    colecao.update_one(
        {"email": email},
        {
            "$set": {
                "status": status,
                "subscription_status": subscription_status,
                "raw_data": data  # salva o payload completo
            }
        },
        upsert=True
    )

    return jsonify({"message": "Email salvo com sucesso!"}), 200
