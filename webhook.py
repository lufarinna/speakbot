from flask import Flask, request
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Conecta ao MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["speakTrainer"]
colecao = db["usuarios_autorizados"]

@app.route("/kiwify", methods=["POST"])
def receber_dados():
    data = request.json
    email = data.get("customer_email")
    status = data.get("status")

    if email and status in ["approved", "active"]:
        if not colecao.find_one({"email": email}):
            colecao.insert_one({"email": email})
            print(f"✅ Novo autorizado salvo no MongoDB: {email}")
        return "Salvo", 200

    return "Ignorado", 200

if __name__ == "__main__":
    app.run()
