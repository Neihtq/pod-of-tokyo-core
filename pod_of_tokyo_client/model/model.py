from pod_of_tokyo_commons.model import UpdateEvent


class Model:
    def __init__(self):
        self.player_name = "<player-name>"
        self.alive = True
        self.game_state = {}
        self.player_stats = {"Health": 0, "Score": 0, "Energy": 0, "Location": ""}
        self.events = []
        self.players = []
        self.dices = []

    def set_view(self, view):
        self.view = view

    def add_event(self, event):
        self.events.append(event)
        self.view.add_event(event)

    def update_player_stats(self, player_update: UpdateEvent):
        print(f"Receive player stats update:\n{player_update.to_dict()}")
        self.player_stats["Health"] += player_update.health
        self.player_stats["Health"] -= player_update.damage
        self.player_stats["Score"] += player_update.score
        self.player_stats["Energy"] += player_update.energy
        self.player_stats["Location"] = player_update.location

        self.player_stats["Health"] = max(0, self.player_stats["Health"])

        self.view.compose_player_stats()

    def update_alive_status(self, is_alive):
        self.alive = is_alive
        if not self.alive:
            self.player_stats["Location"] = "Heaven"

        self.view.compose_player_stats()
