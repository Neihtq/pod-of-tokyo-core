import unittest
from unittest.mock import MagicMock

from pod_of_tokyo_client.model.model import Model


class TestModel(unittest.TestCase):
    def setUp(self):
        self.model = Model()
        self.model.view = MagicMock()

    def test_add_event(self):
        event = "Test event"
        self.model.add_event(event)
        self.assertIn(event, self.model.events)
        self.model.view.add_event.assert_called_once_with(event)

    def test_update_player_stats(self):
        player_update = MagicMock()
        player_update.health = 1
        player_update.damage = 2
        player_update.energy = 3
        player_update.location = "Tokyo"

        self.model.update_player_stats(player_update)

        self.assertEqual(self.model.player_stats["Health"], 1)
        self.assertEqual(self.model.player_stats["Score"], 2)
        self.assertEqual(self.model.player_stats["Energy"], 3)
        self.assertEqual(self.model.player_stats["Location"], "Tokyo")
        self.model.view.compose_player_stats.assert_called_once()
