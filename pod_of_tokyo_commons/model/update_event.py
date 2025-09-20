class UpdateEvent:
    def __init__(self, location, health=0, damage=0, energy=0):
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
