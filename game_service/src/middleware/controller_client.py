from utils import http_utils as http


class ControllerClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def init_game(self, player_ids):
        return http.post(self.base_url, "initGame", {"playerId": player_ids})

    def destroy_tokyo_bay(self):
        return http.post(self.base_url, "destroyTokyoBay")

    def get_pod_url(self, player_id):
        return http.post(self.base_url, "getPodId", {"playerId": player_id})

    def destroy_all(self):
        return http.post(self.base_url, "destroyAll")

    def relocate(self, player_id, location):
        return http.post(
            self.base_url, "relocate", {"playerId": player_id, "location": location}
        )

    def destroy_pod(self, player_id):
        return http.post(self.base_url, "destroyPod", {"player_id": player_id})

    def get_node_states(self):
        """
        Response:
        {
            "tokyoCity": player_id | null,
            "tokyoBay": player_id | null,
            "outside": [player_id]
        }
        """
        return http.post(self.base_url, "getNodeStates")
