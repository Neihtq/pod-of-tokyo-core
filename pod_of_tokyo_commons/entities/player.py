class Player:
    def __init__(
        self, player_state=None, health=None, energy=None, score=None, location=None
    ):
        if player_state:
            self.health = player_state["health"]
            self.energy = player_state["energy"]
            self.score = player_state["score"]
            self.location = player_state["location"]
        else:
            self.health = health
            self.energy = energy
            self.score = score
            self.location = location

    def to_dict(self):
        return {
            "health": self.health,
            "energy": self.energy,
            "score": self.score,
            "location": self.location,
        }
