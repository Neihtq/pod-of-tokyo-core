class Player:
    def __init__(self, player_state):
        self.health = player_state["health"]
        self.energy = player_state["energy"]
        self.score = player_state["score"]
        self.location = player_state["location"]

    def to_dict(self):
        return {
            "health": self.health,
            "energy": self.energy,
            "score": self.score,
            "location": self.location,
        }
