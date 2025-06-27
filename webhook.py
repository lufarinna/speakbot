from flask import Flask, request
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

# Carregar variáveis do .env
load_dotenv()

app = Flask(__name__)

# Obter URI do MongoDB do .env
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri, server_api=ServerApi('1'))
db = client["speaktrainer"]
colecao = db["autorizados"]

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
