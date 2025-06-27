from flask import Flask, request, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)
client = MongoClient(os.environ["MONGO_URI"])
db = client["speakTrainer"]
collection = db["usuarios_autorizados"]

@app.route('/kiwify', methods=['POST'])
def kiwify_webhook():
    data = request.get_json()

    # Mapeia todos os campos enviados pela Kiwify
    customer_email = data.get('customer_email')
    status = data.get('status')
    product_id = data.get('product_id')
    product_name = data.get('product_name')
    price = data.get('price')
    purchase_date = data.get('purchase_date')
    subscription_status = data.get('subscription_status')
    customer_name = data.get('customer_name')
    customer_phone = data.get('customer_phone')

    # Cria o documento completo
    user_data = {
        "email": customer_email,
        "status": status,
        "product_id": product_id,
        "product_name": product_name,
        "price": price,
        "purchase_date": purchase_date,
        "subscription_status": subscription_status,
        "customer_name": customer_name,
        "customer_phone": customer_phone
    }

    collection.update_one(
        {"email": customer_email},
        {"$set": user_data},
        upsert=True
    )

    return jsonify({"message": "Email salvo com sucesso!"})

if __name__ == '__main__':
    app.run(debug=True)
