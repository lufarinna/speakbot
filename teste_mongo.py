from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Sua URI com a senha real
uri = "mongodb+srv://admin:admin123@cluster0.tknkxer.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Cria cliente MongoDB
client = MongoClient(uri, server_api=ServerApi('1'))

# Testa conexão
try:
    client.admin.command('ping')
    print("✅ Conectado com sucesso ao MongoDB!")
except Exception as e:
    print("❌ Erro ao conectar:", e)
