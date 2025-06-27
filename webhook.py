from flask import Flask, request
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
db = client["speakTrainer"]
colecao = db["usuarios"]

app = Flask(__name__)

@app.route("/kiwify", methods=["POST"])
def receber_dados():
    data = request.json

    # Campos essenciais
    email = data.get("customer_email")
    status = data.get("status")

    if not email or not status:
        return "Faltam campos obrigatórios", 400

    documento = {
        "customer_email": email,
        "customer_name": data.get("customer_name"),
        "status": status,
        "subscription_status": data.get("subscription_status"),
        "product_id": data.get("product_id"),
        "product_name": data.get("product_name"),
        "price": data.get("price"),
        "purchase_date": data.get("purchase_date"),
        "next_billing_date": data.get("next_billing_date"),
        "cancellation_date": data.get("cancellation_date"),
        "customer_phone": data.get("customer_phone")
    }

    # Atualiza se já existir, senão insere novo
    colecao.update_one(
        {"customer_email": email},
        {"$set": documento},
        upsert=True
    )

    print(f"✅ Dados atualizados para: {email}")
    return "Salvo com sucesso", 200

if __name__ == "__main__":
    app.run()
