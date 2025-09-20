class UpdateEvent:
    def __init__(self, location, updates=None, health=0, damage=0, energy=0, score=0):
        if updates:
            self.health = int(updates["health"])
            self.damage = int(updates["damage"])
            self.energy = int(updates["energy"])
            self.score = int(updates["score"])
            self.location = updates["location"]
        else:
            self.health = health
            self.damage = damage
            self.energy = energy
            self.score = score
            self.location = location

    def to_dict(self):
        return {
            "health": self.health,
            "damage": self.damage,
            "energy": self.energy,
            "score": self.score,
            "location": self.location,
        }
