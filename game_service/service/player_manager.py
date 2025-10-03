from entities.player import Player
from middleware.pod_client import PodClient


class PlayerManager:
    def __init__(self, player_name_by_id: dict[str, str]):
        self.player_name_by_id = {}  # used for mapping id to pod-name
        self.pod_by_player_id = {}
        self.player_order = []
        self.dead_players = set()

    def get_player_list(self) -> list[Player]:
        return [
            Player(player_id, player_name)
            for (player_id, player_name) in self.player_name_by_id.values()
        ]

    def get_pod(self, player_id: str) -> PodClient:
        return self.pod_by_player_id[player_id]

    def get_player_order(self) -> list:
        return self.player_order

    def get_num_alive(self) -> int:
        return len(self.player_order) - len(self.dead_players)

    def get_player_name(self, player_id: str) -> str:
        return self.get_pod(player_id).name

    def get_current_player_id(self, index: int) -> str:
        return self.player_order[index]

    def get_player_order_length(self) -> int:
        return len(self.player_order)

    def get_player_index(self, player_id: str) -> int:
        return self.player_order.index(player_id)

    def set_pod(self, player_id: str, pod_client: PodClient):
        self.pod_by_player_id[player_id] = pod_client

    def add_to_order(self, player_id: str):
        self.player_order.append(player_id)

    def set_pod_and_add_to_order(self, player_id: str, pod_client: PodClient):
        self.set_pod(player_id, pod_client)
        self.add_to_order(player_id)

    def add_dead_player(self, player_id: str):
        self.dead_players.add(player_id)

    def is_dead(self, player_id: str) -> bool:
        return player_id in self.dead_players

    def remove_player(self, player_id: str):
        if player_id in self.pod_by_player_id:
            del self.pod_by_player_id[player_id]
