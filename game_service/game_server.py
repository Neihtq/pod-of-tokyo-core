import random
from typing import Protocol, cast

from flask import Flask, request
from flask_socketio import SocketIO, join_room
from pod_of_tokyo_commons.constants import MONSTER_NAMES
from pod_of_tokyo_commons.model import MessageType

from game_service.service.game_service import GameService
from game_service.utils.constants import ROOM


class SocketRequest(Protocol):
    sid: str


socket_request = cast(SocketRequest, request)


class GameServer:
    def __init__(self, host="localhost", port=10000, controller_port=11000):
        self.monster_names = list(MONSTER_NAMES)
        random.shuffle(self.monster_names)
        self.host = host
        self.port = port

        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "secret"

        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        self.connections = {}
        self.game_service = GameService(self.socketio, f"{host}:{controller_port}")

        self._register_events()

    def _register_events(self):
        @self.socketio.on("connect")
        def on_connect():
            sid = socket_request.sid
            self.connections[sid] = self.monster_names.pop()
            join_room(ROOM, sid=sid)
            print(f"[+] Added player {sid}")
            self.notify_all()

        @self.socketio.on("disconnect")
        def on_disconnect():
            sid = socket_request.sid
            del self.connections[sid]
            self.game_service.remove(sid)
            print(f"[-] Removed player {sid}")

        @self.socketio.on("get_name")
        def handle_get_name():
            sid = socket_request.sid
            return {"playerName": self.connections[sid]}

        @self.socketio.on("start_game")
        def handle_start_game():
            print("Received message to start game")
            self.game_service.set_players(self.connections.copy())
            self.socketio.start_background_task(self.game_service.game_loop)

    def notify_all(self):
        self.socketio.emit(
            MessageType.LOBBY.value,
            {"members": list(self.connections.values())},
            to=ROOM,
        )

    def run(self):
        self.socketio.run(self.app, host=self.host, port=self.port)
