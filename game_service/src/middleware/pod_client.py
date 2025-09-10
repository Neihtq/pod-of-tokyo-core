from utils import http_utils as http


class PodClient:
    def __init__(self, base_url, name, player_id):
        self.base_url = base_url
        self.name = name
        self.player_id = player_id

    def slap(self, damage=1):
        return http.post(self.base_url, "slap", {"damage": damage})

    def heal(self, life=1):
        return http.post(self.base_url, "heal", {"life": life})

    def update_score(self, score):
        return http.post(self.base_url, "updateScore", {"score": score})

    def update_energy(self, energy):
        return http.post(self.base_url, "updateEnergy", {"energy": energy})

    def get_state(self):
        state = http.post(self.base_url, "getState")
        return (state["health"], state["score"], state["energy"], state["location"])
