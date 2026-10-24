from flask import Flask, request, jsonify, render_template
from src.intent_ml import predict_intent
from src.generator import generate_response

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    text = data.get("text")

    intent = predict_intent(text)
    response = generate_response(text, intent)

    return jsonify({
        "response": response
    })

if __name__ == "__main__":
    app.run(debug=True)