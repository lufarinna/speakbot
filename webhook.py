from flask import Flask, request
import json
import os

app = Flask(__name__)
ARQUIVO = "autorizados.json"

# Cria o arquivo se não existir
if not os.path.exists(ARQUIVO):
    with open(ARQUIVO, "w") as f:
        json.dump([], f)

@app.route("/kiwify", methods=["POST"])
def receber_dados():
    data = request.json
    email = data.get("customer_email")
    status = data.get("status")

    if email and status in ["approved", "active"]:
        with open(ARQUIVO, "r") as f:
            autorizados = json.load(f)

        if email not in autorizados:
            autorizados.append(email)
            with open(ARQUIVO, "w") as f:
                json.dump(autorizados, f)
            print(f"✅ Novo autorizado: {email}")
        return "Salvo", 200

    return "Ignorado", 200

if __name__ == "__main__":
    app.run()
