import unittest
from unittest.mock import patch

from game_service.middleware.pod_client import PodClient


class TestPodClient(unittest.TestCase):

    def setUp(self):
        self.base_url = "http://mock-pod-service"
        self.name = "test-monster"
        self.player_id = "test-player"
        self.client = PodClient(self.base_url, self.name, self.player_id)

    @patch("game_service.utils.http_utils.post")
    def test_slap(self, mock_post):
        mock_post.return_value = {"status": "slapped"}
        damage = 10
        response = self.client.slap(damage)
        mock_post.assert_called_once_with(self.base_url, "slap", {"damage": damage})
        self.assertEqual(response, {"status": "slapped"})

    @patch("game_service.utils.http_utils.post")
    def test_heal(self, mock_post):
        mock_post.return_value = {"status": "healed"}
        health = 5
        response = self.client.heal(health)
        mock_post.assert_called_once_with(self.base_url, "heal", {"health": health})
        self.assertEqual(response, {"status": "healed"})

    @patch("game_service.utils.http_utils.post")
    def test_update_score(self, mock_post):
        mock_post.return_value = {"status": "score updated"}
        points = 100
        response = self.client.update_score(points)
        mock_post.assert_called_once_with(
            self.base_url, "updateScore", {"points": points}
        )
        self.assertEqual(response, {"status": "score updated"})

    @patch("game_service.utils.http_utils.post")
    def test_charge_energy(self, mock_post):
        mock_post.return_value = {"status": "energy charged"}
        energy = 20
        response = self.client.charge_energy(energy)
        mock_post.assert_called_once_with(
            self.base_url, "chargeEnergy", {"energy": energy}
        )
        self.assertEqual(response, {"status": "energy charged"})

    @patch("game_service.utils.http_utils.post")
    def test_get_state(self, mock_post):
        mock_post.return_value = {
            "health": 100,
            "score": 500,
            "energy": 30,
            "location": "tokyo-city",
        }
        health, score, energy, location = self.client.get_state()
        mock_post.assert_called_once_with(self.base_url, "getState")
        self.assertEqual(health, 100)
        self.assertEqual(score, 500)
        self.assertEqual(energy, 30)
        self.assertEqual(location, "tokyo-city")
