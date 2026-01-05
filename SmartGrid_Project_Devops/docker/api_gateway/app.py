from flask import Flask, jsonify, request

app = Flask(__name__)

# Simulated JWT check
@app.before_request
def check_jwt():
    token = request.headers.get("Authorization")
    if token != "Bearer mysecrettoken":
        return jsonify({"error": "Unauthorized"}), 401

@app.route("/api/test")
def test():
    return jsonify({"message": "API Gateway working!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
