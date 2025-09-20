import unittest
from unittest.mock import MagicMock, patch

from pod_of_tokyo_commons.entities import DiceSymbols

from game_service.model import Location
from game_service.service.game_service import GameService


class TestGameService(unittest.TestCase):
    def setUp(self):
        """
        Set up a new GameService instance for each test.
        """
        self.socketio = MagicMock()
        self.controller_url = "http://localhost:5001"
        self.game_service = GameService(self.socketio, self.controller_url)

    @patch("game_service.service.game_service.join_room")
    def test_add_player(self, mock_join_room):
        """
        Tests that a player can be added to the game.
        """
        sid = "player1_sid"
        self.game_service.add(sid)
        self.assertIn(sid, self.game_service.players)
        self.assertIsNone(self.game_service.players[sid])
        mock_join_room.assert_called_once()

    @patch("game_service.service.game_service.join_room")
    def test_remove_player(self, mock_join_room):
        """
        Tests that a player can be removed from the game.
        """
        sid = "player1_sid"
        self.game_service.add(sid)
        self.game_service.remove(sid)
        self.assertNotIn(sid, self.game_service.players)

    @patch("game_service.utils.http_utils.post")
    @patch("game_service.service.game_service.ControllerClient")
    def test_start_game(self, mock_controller_client, mock_http_post):
        """
        Tests the start_game method to ensure it correctly initializes the game state.
        """
        # Arrange
        mock_http_post.return_value = {
            "players": [
                {"playerId": "player1", "podUrl": "http://pod1", "name": "Monster1"},
                {"playerId": "player2", "podUrl": "http://pod2", "name": "Monster2"},
            ],
            "locations": {
                "tokyo-city": "node1",
                "tokyo-bay": "node2",
                "outside": "node3",
            },
        }
        self.game_service.players = {"player1": None, "player2": None}
        self.game_service.player_order = []

        # Act
        self.game_service.start_game()

        # Assert
        self.assertEqual(len(self.game_service.player_order), 2)
        self.assertIn("player1", self.game_service.players)
        self.assertIn("player2", self.game_service.players)
        self.assertIsNotNone(self.game_service.players["player1"])
        self.assertIsNotNone(self.game_service.players["player2"])

    def test_is_in_tokyo(self):
        self.game_service.locations = {
            "node1": Location.CITY,
            "node2": Location.BAY,
            "node3": Location.OUTSIDE,
        }
        self.assertTrue(self.game_service.is_in_tokyo("node1"))
        self.assertTrue(self.game_service.is_in_tokyo("node2"))
        self.assertFalse(self.game_service.is_in_tokyo("node3"))

    def test_check_winner(self):
        pod = MagicMock()
        pod.player_id = "player1"
        pod.get_state.return_value = (10, 0, 0, "node1")

        pod3 = MagicMock()
        pod3.player_id = "player3"
        pod3.name = "Monster3"
        pod3.get_state.return_value = (10, 0, 0, "node3")
        self.game_service.players = {"player1": pod, "player3": pod3}

        self.game_service.dead = {"player2"}
        self.game_service.player_order = ["player1", "player2", "player3"]

        # Test winning by score
        self.assertTrue(self.game_service.check_winner(pod, 20))

        # Test winning by last one standing
        self.game_service.dead = {"player2", "player3"}
        self.assertTrue(self.game_service.check_winner(pod, 10))

        # Test no winner
        self.game_service.dead = {"player2"}
        self.assertFalse(self.game_service.check_winner(pod, 10))

    @patch("game_service.service.game_service.roll_dices")
    def test_reroll_dices(self, mock_roll_dices):
        pod = MagicMock()
        pod.player_id = "player1"
        pod.name = "Monster1"
        self.game_service.players = {"player1": pod}
        self.game_service.socketio.call.return_value = {
            "dicesToKeep": [DiceSymbols.FIST, DiceSymbols.FIST]
        }
        mock_roll_dices.return_value = [
            DiceSymbols.FIST,
            DiceSymbols.FIST,
            DiceSymbols.ONE,
            DiceSymbols.TWO,
            DiceSymbols.THREE,
            DiceSymbols.HEART,
        ]

        dices = self.game_service.reroll_dices(pod)

        self.assertEqual(len(dices), 6)  # 2 + 2 + 2
        self.assertEqual(self.game_service.socketio.call.call_count, 3)

    def test_resolve_dices(self):
        pod = MagicMock()
        pod.player_id = "player1"
        pod.name = "Monster1"
        dices = [
            DiceSymbols.HEART.value,
            DiceSymbols.FIST.value,
            DiceSymbols.FIST.value,
            DiceSymbols.THUNDER.value,
            DiceSymbols.ONE.value,
            DiceSymbols.ONE.value,
            DiceSymbols.ONE.value,
        ]
        self.game_service.resolve_dices(pod, dices, "node1")

        pod.heal.assert_called_once_with(life=1)
        pod.charge_energy.assert_called_once_with(energy=1)
        pod.update_score.assert_called_once_with(score=3)
        self.assertEqual(self.game_service.socketio.emit.call_count, 2)

    @patch(
        "game_service.service.game_service.GameService.is_in_tokyo", return_value=False
    )
    def test_slap(self, mock_is_in_tokyo):
        pod1 = MagicMock()
        pod1.player_id = "player1"
        pod1.name = "Monster1"
        pod1.get_state.return_value = (10, 0, 0, "node1")

        pod2 = MagicMock()
        pod2.player_id = "player2"
        pod2.name = "Monster2"
        pod2.get_state.return_value = (10, 0, 0, "node2")

        pod3 = MagicMock()
        pod3.player_id = "player3"
        pod3.name = "Monster3"
        pod3.get_state.return_value = (10, 0, 0, "node3")

        self.game_service.players = {
            "player1": pod1,
            "player2": pod2,
            "player3": pod3,
        }
        self.game_service.player_order = ["player1", "player2", "player3"]
        self.game_service.dead = set()

        self.game_service.slap(pod1, "node1", 2)

        pod2.slap.assert_called_once_with(2)
        pod3.slap.assert_called_once_with(2)


if __name__ == "__main__":
    unittest.main()
