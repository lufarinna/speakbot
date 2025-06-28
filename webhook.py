# NOVO CONTEÚDO PARA SEU webhook.py
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import os
import sys
from datetime import datetime # IMPORTANTE: Adicione esta linha!-

app = Flask(__name__)

# --- Configuração do MongoDB ---
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("❌ ERRO: Variável de ambiente MONGO_URI não encontrada.")
    print("Por favor, configure MONGO_URI nas Config Vars do Heroku.")
    sys.exit(1)

try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    print("✅ Conexão com MongoDB estabelecida com sucesso!")
except ConnectionFailure as e:
    print(f"❌ ERRO de Conexão com MongoDB: {e}")
    print("Verifique sua MONGO_URI e as configurações de rede do MongoDB Atlas.")
    sys.exit(1)
except OperationFailure as e:
    print(f"❌ ERRO de Operação MongoDB (autenticação/autorização): {e}")
    print("Verifique suas credenciais no MONGO_URI.")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERRO inesperado ao conectar ao MongoDB: {e}")
    sys.exit(1)

db = client["speakTrainer"]
collection = db["usuarios_autorizados"]

# --- Rotas da Aplicação ---
@app.route('/kiwify', methods=['POST'])
def kiwify_webhook():
    try:
        data = request.get_json()
        print("📩 Webhook recebido:", data)

        if not data:
            print("⚠️ Nenhum dado recebido no corpo da requisição.")
            return jsonify({"error": "Invalid data"}), 400

        customer_email = data.get('customer_email')
        status = data.get('status')
        product_id = data.get('product_id')
        product_name = data.get('product_name')
        price = data.get('price')
        purchase_date = data.get('purchase_date')
        subscription_status = data.get('subscription_status')
        customer_name = data.get('customer_name')
        customer_phone = data.get('customer_phone')

        if not customer_email:
            print("⚠️ Webhook recebido sem 'customer_email'. Ignorando.")
            return jsonify({"message": "Missing customer_email"}), 400

        user_data = {
            "email": customer_email,
            "status": status,
            "product_id": product_id,
            "product_name": product_name,
            "price": price,
            "purchase_date": purchase_date,
            "subscription_status": subscription_status,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "last_updated": datetime.utcnow() # Adicionado para auditoria
        }

        collection.update_one(
            {"email": customer_email},
            {"$set": user_data},
            upsert=True
        )
        print(f"✅ Dados para {customer_email} salvos/atualizados no MongoDB.")
        return jsonify({"message": "Dados do cliente processados com sucesso!"}), 200

    except Exception as e:
        print(f"❌ ERRO no processamento do webhook: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Remova ou comente este bloco:
# if __name__ == '__main__':
#     app.run(debug=True)