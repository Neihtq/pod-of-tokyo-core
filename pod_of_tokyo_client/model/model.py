class Model:
    def __init__(self):
        self.game_state = {}
        self.player_stats = {"Health": 0, "Score": 0, "Energy": 0}
        self.events = []
        self.players = []
        self.dices = []

    def set_view(self, view):
        self.view = view

    def add_event(self, event):
        self.events.append(event)
        self.view.add_event(event)

    def update_player_stats(self, health, score, energy=0):
        self.player_stats["Health"] += health
        self.player_stats["Score"] += score
        self.player_stats["Energy"] += energy
        self.view.compose_player_stats()
