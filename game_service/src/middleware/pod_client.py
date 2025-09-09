from utils import http_utils as http


class PodClient:
    def __int__(self, base_url):
        self.base_url = base_url

    def slap(self, damage=1):
        return http.post(self.base_url, "slap", {"damage": damage})

    def heal(self, life=1):
        return http.post(self.base_url, "heal", {"life": life})
