"""
PKTron Agent — simple backend server.
Run: python3 server.py
Then open index.html in a browser (or serve it from the same folder).
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from agent import run_pktron_agent, CIRCUIT_MENU

app = Flask(__name__)
CORS(app)  # allow the plain-HTML front end to call this from the browser


@app.route("/menu", methods=["GET"])
def menu():
    return jsonify(CIRCUIT_MENU)


@app.route("/run", methods=["POST"])
def run():
    data = request.get_json(force=True)
    user_request = (data or {}).get("request", "").strip()
    if not user_request:
        return jsonify({"success": False, "message": "Please type a request."}), 400
    output = run_pktron_agent(user_request)
    return jsonify(output)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
