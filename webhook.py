from flask import Flask, request
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()

# Conectar ao MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["speaktrainer"]
collection = db["autorizados"]

app = Flask(__name__)

@app.route("/kiwify", methods=["POST"])
def receber_dados():
    data = request.json
    email = data.get("customer_email")
    status = data.get("status")

    if email and status in ["approved", "active"]:
        # Verifica se já está salvo
        if not collection.find_one({"email": email}):
            collection.insert_one({"email": email})
            print(f"✅ Novo autorizado salvo: {email}")
        return "Salvo", 200

    return "Ignorado", 200

if __name__ == "__main__":
    app.run()
