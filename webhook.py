from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

# Carrega variáveis do .env
load_dotenv()

# Conexão com MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client["kiwify"]
collection = db["assinantes"]

# Inicializa o app Flask
app = Flask(__name__)

@app.route("/kiwify", methods=["POST"])
def receber_webhook():
    try:
        dados = request.get_json()

        if not dados:
            return jsonify({"error": "Requisição inválida. Nenhum dado JSON recebido."}), 400

        email = dados.get("customer_email")
        if not email:
            return jsonify({"error": "Campo 'customer_email' é obrigatório."}), 400

        # Salva ou atualiza os dados no MongoDB
        collection.update_one(
            {"customer_email": email},
            {"$set": dados},
            upsert=True
        )

        return jsonify({"message": "Dados salvos com sucesso!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Executar localmente
if __name__ == "__main__":
    app.run(debug=True, port=5000)
