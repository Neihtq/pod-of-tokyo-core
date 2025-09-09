from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route("/")
def hello():
    return "Hello, World!"


@socketio.on("connect")
def handle_connect():
    print("Client connedted")
    emit("response", {"data": "Connected to server"})


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")


if __name__ == "__main__":
    socketio.run(app)
