from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Carregar variáveis do .env
load_dotenv()

# Inicializa o Flask
app = Flask(__name__)

# Conexão com MongoDB
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client["speakTrainer"]
colecao = db["usuarios_autorizados"]

# Rota do webhook
@app.route("/kiwify", methods=["POST"])
def kiwify_webhook():
    data = request.get_json()
    print("📩 Webhook recebido:", data)

    if not data:
        print("⚠️ Nenhum dado recebido.")
        return jsonify({"error": "Dados ausentes"}), 400

    customer_email = data.get("customer_email")
    status = data.get("status")

    if customer_email and status:
        doc = {
            "email": customer_email,
            "status": status
        }
        result = colecao.insert_one(doc)
        print("✅ Documento salvo com ID:", result.inserted_id)
        return jsonify({"message": "Dados salvos com sucesso!"}), 200
    else:
        print("⚠️ Campos obrigatórios ausentes")
        return jsonify({"message": "Requisição incompleta"}), 400

if __name__ == "__main__":
    app.run()
