from typing import Protocol, cast

from flask import Flask, request
from flask_socketio import SocketIO, emit
from service.game_service import GameService


class SocketRequest(Protocol):
    sid: str


socket_request = cast(SocketRequest, request)


class GameServer:
    def __init__(self, host="0.0.0.0", port=5000, controller_port=6000):
        self.host = host
        self.port = port

        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "secret"

        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.game_service = GameService(self.socketio, f"{host}:{controller_port}")

        self._register_events()

    def _register_events(self):

        @self.socketio.on("connect")
        def on_connect():
            sid = socket_request.sid
            self.game_service.add(sid)

        @self.socketio.on("disconnect")
        def on_disconnect():
            sid = socket_request.sid
            self.game_service.remove(sid)

        @self.socketio.on("start game")
        def handle_start_game(json):
            print("Starting game")
            self.socketio.start_background_task(self.game_service.game_loop)

    def run(self):
        self.socketio.run(self.app, host=self.host, port=self.port)
