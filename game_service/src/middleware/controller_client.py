from utils import http_utils as http
from utils.http_utils import join


class ControllerClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def init_game(self, player_ids):
        return http.post(join(self.base_url, "initGame"), {"data": player_ids})

    def destroy_tokyo_bay(self):
        return http.delete(join(self.base_url, "destroyTokyoBay"))

    def get_pod_url(self, player_id):
        return http.get(join(self.base_url, "getPodId"), {"data": player_id})
