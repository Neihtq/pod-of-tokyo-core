from entities.player import Player


class PlayerManager:
    def __init__(self, player_name_by_id: dict[str, str]):
        self.player_name_by_id = {}  # used for mapping id to pod-name
        self.pod_by_player_id = {}
        self.player_order = {}
        self.dead_players = set()

    def get_player_list(self) -> list[Player]:
        return [
            Player(player_id, player_name)
            for (player_id, player_name) in self.player_name_by_id.values()
        ]
