class UpdateEvent:
    def __init__(self, location, updates=None, health=0, damage=0, energy=0):
        if updates:
            self.health = updates["health"]
            self.damage = updates["damage"]
            self.energy = updates["energy"]
            self.location = updates["location"]
        else:
            self.health = health
            self.damage = damage
            self.energy = energy
            self.location = location

    def to_dict(self):
        return {
            "health": self.health,
            "damage": self.damage,
            "energy": self.energy,
            "location": self.location,
        }
