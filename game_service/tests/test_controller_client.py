import unittest
from unittest.mock import patch

from game_service.middleware.controller_client import ControllerClient


class TestControllerClient(unittest.TestCase):

    def setUp(self):
        self.base_url = "http://mock-controller-service"
        self.client = ControllerClient(self.base_url)

    @patch("game_service.utils.http_utils.post")
    def test_init_game(self, mock_post):
        mock_post.return_value = {"status": "game initialized"}
        players_data = [{"name": "player1"}, {"name": "player2"}]
        response = self.client.init_game(players_data)
        mock_post.assert_called_once_with(
            self.base_url, "initGame", {"players": players_data}
        )
        self.assertEqual(response, {"status": "game initialized"})

    @patch("game_service.utils.http_utils.post")
    def test_destroy_tokyo_bay(self, mock_post):
        mock_post.return_value = {"status": "tokyo bay destroyed"}
        response = self.client.destroy_tokyo_bay()
        mock_post.assert_called_once_with(self.base_url, "destroyTokyoBay")
        self.assertEqual(response, {"status": "tokyo bay destroyed"})

    @patch("game_service.utils.http_utils.post")
    def test_get_pod_url(self, mock_post):
        mock_post.return_value = {"podUrl": "http://pod-url"}
        player_id = "player1"
        response = self.client.get_pod_url(player_id)
        mock_post.assert_called_once_with(
            self.base_url, "getPodUrl", {"playerId": player_id}
        )
        self.assertEqual(response, {"podUrl": "http://pod-url"})

    @patch("game_service.utils.http_utils.post")
    def test_destroy_all(self, mock_post):
        mock_post.return_value = {"status": "all destroyed"}
        response = self.client.destroy_all()
        mock_post.assert_called_once_with(self.base_url, "destroyAll")
        self.assertEqual(response, {"status": "all destroyed"})

    @patch("game_service.utils.http_utils.post")
    def test_relocate(self, mock_post):
        mock_post.return_value = {"status": "relocated"}
        player_id = "player1"
        from_location = "outside"
        target_location = "tokyo-city"
        response = self.client.relocate(player_id, from_location, target_location)
        mock_post.assert_called_once_with(
            self.base_url,
            "relocate",
            {
                "playerId": player_id,
                "currentLocation": from_location,
                "targetLocation": target_location,
            },
        )
        self.assertEqual(response, {"status": "relocated"})

    @patch("game_service.utils.http_utils.post")
    def test_destroy_pod(self, mock_post):
        mock_post.return_value = {"status": "pod destroyed"}
        player_id = "player1"
        location = "outside"
        response = self.client.destroy_pod(player_id, location)
        mock_post.assert_called_once_with(
            self.base_url, "destroyPod", {"player_id": player_id, "location": location}
        )
        self.assertEqual(response, {"status": "pod destroyed"})

    @patch("game_service.utils.http_utils.post")
    def test_get_node_state(self, mock_post):
        mock_post.return_value = {
            "tokyoCity": "player1",
            "tokyoBay": None,
            "outside": [],
        }
        response = self.client.get_node_state()
        mock_post.assert_called_once_with(self.base_url, "getNodeState")
        self.assertEqual(
            response, {"tokyoCity": "player1", "tokyoBay": None, "outside": []}
        )
