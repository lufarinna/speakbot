from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import os
import sys # Para usar sys.exit() para encerrar a aplicação se a URI não for encontrada

app = Flask(__name__)

# --- Configuração do MongoDB ---
# Pega a URI do MongoDB das variáveis de ambiente do Heroku
MONGO_URI = os.getenv("MONGO_URI")

# Verifica se a MONGO_URI foi carregada. Se não, o app não deve nem iniciar.
if not MONGO_URI:
    print("❌ ERRO: Variável de ambiente MONGO_URI não encontrada.")
    print("Por favor, configure MONGO_URI nas Config Vars do Heroku.")
    sys.exit(1) # Encerra a aplicação para evitar crashes posteriores

try:
    client = MongoClient(MONGO_URI)
    # Tenta um comando simples para verificar a conexão na inicialização
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

        # Mapeia todos os campos relevantes enviados pela Kiwify
        # Ajuste conforme a documentação da Kiwify para ter certeza dos nomes
        customer_email = data.get('customer_email')
        status = data.get('status') # Status geral da compra (e.g., approved, refunded)
        product_id = data.get('product_id')
        product_name = data.get('product_name')
        price = data.get('price')
        purchase_date = data.get('purchase_date')
        subscription_status = data.get('subscription_status') # Status da assinatura (e.g., active, canceled)
        customer_name = data.get('customer_name')
        customer_phone = data.get('customer_phone')
        # Adicione outros campos se necessário, como 'transaction_id', 'plan_id', etc.
        # Ex: transaction_id = data.get('transaction_id')

        # Verifica se o email do cliente está presente, que é o campo chave para o upsert
        if not customer_email:
            print("⚠️ Webhook recebido sem 'customer_email'. Ignorando.")
            return jsonify({"message": "Missing customer_email"}), 400

        # Cria o documento completo para upsert
        user_data = {
            "email": customer_email,
            "status": status, # Status da última compra/evento
            "product_id": product_id,
            "product_name": product_name,
            "price": price,
            "purchase_date": purchase_date,
            "subscription_status": subscription_status, # Status atual da assinatura
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            # "transaction_id": transaction_id, # Se você adicionar
            "last_updated": datetime.utcnow() # Adiciona um timestamp para auditoria
        }

        # Usa update_one com upsert=True para inserir ou atualizar
        # Isso é ideal para rastrear o status de assinaturas
        collection.update_one(
            {"email": customer_email}, # Filtro para encontrar o documento
            {"$set": user_data},      # Atualiza/insere os dados
            upsert=True               # Se não encontrar, insere um novo documento
        )
        print(f"✅ Dados para {customer_email} salvos/atualizados no MongoDB.")
        return jsonify({"message": "Dados do cliente processados com sucesso!"}), 200

    except Exception as e:
        print(f"❌ ERRO no processamento do webhook: {e}")
        # Retorna um 500 para indicar que algo deu errado no servidor
        return jsonify({"error": "Internal server error"}), 500

# Adicionado para facilitar a importação pelo Gunicorn
# 'app' já está definido no início do script
# if __name__ == '__main__':
#     # O modo debug=True não deve ser usado em produção (Heroku)
#     app.run(debug=True)