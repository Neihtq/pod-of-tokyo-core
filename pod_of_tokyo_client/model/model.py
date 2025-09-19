class Model:
    def __init__(self):
        self.game_state = {}
        self.player_stats = {}
        self.events = []
        self.players = []
        self.dices = []

    def set_view(self, view):
        self.view = view

    def add_event(self, event):
        self.events.append(event)
        self.view.add_event(event)
