from werkzeug.exceptions import NotFound

from game_service.entities.player import Player
from game_service.middleware.pod_client import PodClient


class PlayerManager:
    def __init__(self, player_name_by_id: dict[str, str]):
        self.player_name_by_id = player_name_by_id  # used for mapping id to pod-name
        self.pod_by_player_id = {}
        self.player_order = []
        self.dead_players = set()

    def __validate_player_id__(self, player_id):
        if player_id not in self.player_name_by_id:
            raise NotFound(f"Player with id '{player_id}' does not exist")
        if player_id not in self.pod_by_player_id:
            raise NotFound(f"Player with id '{player_id}' does not have a pod")

    def set_pod(self, player_id: str, pod_client: PodClient):
        if player_id not in self.player_name_by_id:
            raise NotFound(f"Player with id '{player_id}' does not exist")
        self.pod_by_player_id[player_id] = pod_client

    def add_to_order(self, player_id: str):
        self.__validate_player_id__(player_id)
        self.player_order.append(player_id)

    def set_pod_and_add_to_order(self, player_id: str, pod_client: PodClient):
        self.set_pod(player_id, pod_client)
        self.add_to_order(player_id)

    def add_dead_player(self, player_id: str):
        self.__validate_player_id__(player_id)
        self.dead_players.add(player_id)

    def is_dead(self, player_id: str) -> bool:
        return player_id in self.dead_players

    def remove_player(self, player_id: str):
        if player_id in self.pod_by_player_id:
            del self.pod_by_player_id[player_id]

    def get_player_list(self) -> list[Player]:
        return [
            Player(player_id, player_name)
            for (player_id, player_name) in self.player_name_by_id.items()
        ]

    def get_pod(self, player_id: str) -> PodClient:
        self.__validate_player_id__(player_id)
        return self.pod_by_player_id[player_id]

    def get_player_order(self) -> list:
        return self.player_order

    def get_num_alive(self) -> int:
        return len(self.player_order) - len(self.dead_players)

    def get_player_name(self, player_id: str) -> str:
        return self.get_pod(player_id).name

    def get_player_at_index(self, index: int) -> str:
        if index >= len(self.player_order):
            raise IndexError(f"Index {index} out of range")
        return self.player_order[index]

    def get_number_of_players(self) -> int:
        return len(self.player_order)

    def get_player_index(self, player_id: str) -> int:
        return self.player_order.index(player_id)
