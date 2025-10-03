import time
from collections import defaultdict

from pod_of_tokyo_commons.entities import GameState, Player
from pod_of_tokyo_commons.model.message_type import MessageType

from game_service.utils.constants import ROOM
from service.player_manager import PlayerManager


class NotificationService:
    def __init__(self, sio, manager: PlayerManager):
        self.sio = sio
        self.manager = manager

    def _emit_message(self, command: MessageType, recipient: str, payload: dict = {}):
        self.sio.emit(command.value, payload, to=recipient)

    def call_and_wait(self, command: MessageType, player_id: str, payload={}):
        response = self.sio.call(command.value, payload, to=player_id, timeout=600)[
            "response"
        ]
        return response

    def get_game_state(self):
        game_state = defaultdict(list)
        for p_id in self.manager.player_order:
            if self.manager.is_dead(p_id):
                continue

            pod = self.manager.get_pod(p_id)
            health, score, energy, location = pod.get_state()
            game_state[location].append(
                Player(
                    health=health,
                    score=score,
                    energy=energy,
                    location=location,
                    name=pod.name,
                )
            )
        return GameState(game_state)

    def notify_all(self, message: str):
        game_state = self.get_game_state().to_dict()
        payload = {"message": message, "gameState": game_state}
        self._emit_message(
            command=MessageType.EVENT,
            recipient=ROOM,
            payload=payload,
        )
        time.sleep(1.0)

    def notify_death(self, player_id):
        self._emit_message(command=MessageType.DEATH, recipient=player_id)

    def send_player_update(self, player_update, player_id):
        payload = {"update": player_update.to_dict()}
        self._emit_message(
            command=MessageType.UPDATE,
            recipient=player_id,
            payload=payload,
        )

    def notify_game_start(self):
        self._emit_message(command=MessageType.START_GAME, recipient=ROOM)

    def notify_turn_end(self, player_id):
        self._emit_message(command=MessageType.END_TURN, recipient=player_id)

    def notify_game_end(self, winner_name: str):
        self._emit_message(
            command=MessageType.END_GAME,
            recipient=ROOM,
            payload={"winner": winner_name},
        )
