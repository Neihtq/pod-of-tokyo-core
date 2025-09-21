from pod_of_tokyo_commons.model.location import Location


class UpdateEvent:
    def __init__(
        self,
        location=Location.OUTSIDE,
        updates=None,
        health=0,
        damage=0,
        energy=0,
        score=0,
    ):
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
            self.location = location.value

    def to_dict(self):
        return {
            "health": self.health,
            "damage": self.damage,
            "energy": self.energy,
            "score": self.score,
            "location": self.location,
        }
