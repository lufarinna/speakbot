from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client["speakTrainer"]
colecao = db["usuarios_autorizados"]

@app.route("/kiwify", methods=["POST"])
def kiwify_webhook():
    data = request.get_json()
    print("📩 Webhook recebido:", data)

    if not data:
        print("⚠️ Nenhum dado recebido no corpo da requisição.")
        return jsonify({"error": "Invalid data"}), 400

    customer_email = data.get("customer_email")
    status = data.get("status")

    if customer_email and status == "approved":
        doc = {"email": customer_email}
        result = colecao.insert_one(doc)
        print("✅ Email salvo no MongoDB com ID:", result.inserted_id)
        return jsonify({"message": "Email salvo com sucesso!"}), 200
    else:
        print("⚠️ Dados incompletos ou status diferente de 'approved'")
        return jsonify({"message": "Requisição ignorada"}), 200
