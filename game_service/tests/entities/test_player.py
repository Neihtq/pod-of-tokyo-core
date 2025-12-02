import unittest
from game_service.entities.player import Player

class TestPlayer(unittest.TestCase):
    def test_init(self):
        player = Player("p1", "Player 1")
        self.assertEqual(player.player_id, "p1")
        self.assertEqual(player.player_name, "Player 1")

    def test_equality(self):
        p1 = Player("p1", "Player 1")
        p2 = Player("p1", "Player 1")
        p3 = Player("p2", "Player 2")
        
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)
        self.assertNotEqual(p1, "some string")
