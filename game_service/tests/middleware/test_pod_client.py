import unittest
from unittest.mock import patch

from game_service.middleware.pod_client import PodClient


class TestPodClient(unittest.TestCase):
    def setUp(self):
        base_url = "some.test.url"
        player_name = "playerName"
        player_id = "playerId"
        self.client = PodClient(base_url, player_name, player_id)

    def test_init_pod_client(self):
        self.assertEqual(self.client.base_url, "some.test.url")
        self.assertEqual(self.client.name, "playerName")
        self.assertEqual(self.client.player_id, "playerId")

    @patch("game_service.utils.http_utils")
    def test_slap(self, mock_http_utils):
        response = {"health": 0}
        mock_http_utils.post.return_value = response
        damage = 10

        result = self.client.slap(damage)

        expected = {"health": 0}
        self.assertEqual(result, expected)

    @patch("game_service.utils.http_utils")
    def test_heal(self, mock_http_utils):
        response = {"health": 10}
        mock_http_utils.post.return_value = response
        heal_amount = 10

        result = self.client.heal(heal_amount)

        expected = {"health": 10}
        self.assertEqual(result, expected)

    @patch("game_service.utils.http_utils")
    def test_update_score(self, mock_http_utils):
        response = {"score": 5}
        mock_http_utils.post.return_value = response
        score = 5

        result = self.client.update_score(score)

        expected = {"score": 5}
        self.assertEqual(result, expected)

    @patch("game_service.utils.http_utils")
    def test_charge_energy(self, mock_http_utils):
        response = {"energy": 5}
        mock_http_utils.post.return_value = response
        score = 5

        result = self.client.charge_energy(score)

        expected = {"energy": 5}
        self.assertEqual(result, expected)

    @patch("game_service.utils.http_utils")
    def test_get_state(self, mock_http_utils):
        response = {
            "name": "someName",
            "health": 10,
            "score": 10,
            "energy": 10,
            "location": "outside",
        }
        mock_http_utils.post.return_value = response

        result = self.client.get_state()

        expected = {
            "name": "someName",
            "health": 10,
            "score": 10,
            "energy": 10,
            "location": "outside",
        }
        self.assertEqual(result, expected)
