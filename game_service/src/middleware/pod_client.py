from utils import http_utils as http


class PodClient:
    def __int__(self, base_url, name):
        self.base_url = base_url
        self.name = name

    def slap(self, damage=1):
        return http.post(self.base_url, "slap", {"damage": damage})

    def heal(self, life=1):
        return http.post(self.base_url, "heal", {"life": life})

    def update_score(self, score):
        return http.post(self.base_url, "updateScore", {"score": score})

    def update_energy(self, energy):
        return http.post(self.base_url, "updateEnergy", {"energy": energy})

    def get_life(self):
        return http.post(self.base_url, "getLife")

    def get_score(self):
        return http.post(self.base_url, "getScore")

    def get_energy(self):
        return http.post(self.base_url, "get")
