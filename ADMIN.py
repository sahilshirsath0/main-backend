from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from config import Config  # Importing your config

app = Flask(__name__)
app.config.from_object(Config)  # Load config from config.py

# Enable CORS for frontend communication
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173")

# Sample route
@app.route("/api/data", methods=["GET"])
def get_data():
    return jsonify({"message": "API is working!"})

# Handle Socket.IO connection
@socketio.on("connect")
def handle_connect():
    print("Client connected")
    emit("message", {"msg": "Connected to the server"})

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")

@socketio.on("custom_event")
def handle_custom_event(data):
    print("Received event:", data)
    emit("response", {"msg": "Data received"}, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
