from flask import Flask, request

app = Flask(__name__)

@app.route("/kiwify", methods=["POST"])
def receber_dados():
    data = request.json
    print("🚨 DADOS RECEBIDOS DA KIWIFY:")
    print(data)
    return "OK", 200

if __name__ == "__main__":
    app.run()
