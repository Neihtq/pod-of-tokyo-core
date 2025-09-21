import unittest
from unittest.mock import MagicMock, patch

from pod_of_tokyo_commons.entities import DiceSymbols
from pod_of_tokyo_commons.model import MessageType

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
    def test_remove_player(self, mock_join_room):
        """
        Tests that a player can be removed from the game.
        """
        sid = "player1_sid"
        self.game_service.players[sid] = "Monster"
        self.game_service.remove(sid)
        self.assertNotIn(sid, self.game_service.players)

    @patch("game_service.utils.http_utils.post")
    @patch("game_service.service.game_service.ControllerClient")
    def test_start_game(self, mock_controller_client, mock_http_post):
        """
        Tests the start_game method to ensure it correctly initializes the game state.
        """
        # Arrange
        mock_http_post.side_effect = [
            {  # First call to init_game
                "players": [
                    {
                        "playerId": "player1",
                        "podUrl": "http://pod1",
                        "name": "Monster1",
                    },
                    {
                        "playerId": "player2",
                        "podUrl": "http://pod2",
                        "name": "Monster2",
                    },
                ],
                "locations": {
                    "tokyo-city": "node1",
                    "tokyo-bay": "node2",
                    "outside": "node3",
                },
            },
            # Subsequent calls from get_state()
            {
                "health": 10,
                "score": 0,
                "energy": 0,
                "location": "node3",
            },  # For player 1
            {
                "health": 10,
                "score": 0,
                "energy": 0,
                "location": "node3",
            },  # For player 2
        ]
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
        self.assertEqual(self.game_service.socketio.emit.call_count, 6)

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

    def test_resolve_dices_with_slap(self):
        pod1 = MagicMock()
        pod1.player_id = "player1"
        pod1.name = "Monster1"
        pod1.get_state.return_value = (10, 0, 0, "node1")

        pod2 = MagicMock()
        pod2.player_id = "player2"
        pod2.name = "Monster2"
        pod2.get_state.return_value = (10, 0, 0, "node2")

        self.game_service.players = {
            "player1": pod1,
            "player2": pod2,
        }
        self.game_service.player_order = ["player1", "player2"]
        self.game_service.dead = set()
        self.game_service.locations = {
            "node1": Location.CITY,
            "node2": Location.OUTSIDE,
        }

        dices = [
            DiceSymbols.FIST.value,
            DiceSymbols.FIST.value,
        ]
        self.game_service.resolve_dices(pod1, dices, "node1")

        pod2.slap.assert_called_once_with(2)

    def test_game_loop_winner_exists(self):
        self.game_service.start_game = MagicMock()
        self.game_service.decide_starter = MagicMock(return_value=0)
        self.game_service.start_turn = MagicMock()
        self.game_service.player_order = ["player1"]
        player_mock = MagicMock()
        player_mock.get_state.return_value = (10, 0, 0, "node1")
        self.game_service.players = {"player1": player_mock}
        self.game_service.controller.destroy_all = MagicMock()

        # Simulate a winner to exit the loop
        winner_pod = MagicMock()
        winner_pod.name = "player1"
        self.game_service.winner = winner_pod
        self.game_service.game_loop()

        self.game_service.start_game.assert_called_once()
        self.game_service.decide_starter.assert_called_once()
        self.game_service.start_turn.assert_not_called()  # Loop is skipped because winner is already set

    def test_game_loop(self):
        self.game_service.start_game = MagicMock()
        self.game_service.decide_starter = MagicMock(return_value=0)
        self.game_service.start_turn = MagicMock()
        self.game_service.player_order = ["player1"]
        player_mock = MagicMock()
        player_mock.get_state.return_value = (10, 0, 0, "node1")
        self.game_service.players = {"player1": player_mock}
        self.game_service.controller.destroy_all = MagicMock()

        # Test the loop itself
        winner_pod = MagicMock()
        winner_pod.name = "player1"
        self.game_service.winner = None

        def set_winner(player_id):
            self.game_service.winner = winner_pod

        self.game_service.start_turn.side_effect = set_winner
        self.game_service.game_loop()
        self.game_service.start_turn.assert_called_once_with("player1")

    def test_start_turn_in_tokyo(self):
        pod = MagicMock()
        pod.player_id = "player1"
        pod.get_state.return_value = (10, 0, 0, "node1")
        self.game_service.players = {"player1": pod}
        self.game_service.locations = {"node1": Location.CITY}
        self.game_service.is_in_tokyo = MagicMock(return_value=True)
        self.game_service.reroll_dices = MagicMock(return_value=[])
        self.game_service.resolve_dices = MagicMock()
        self.game_service.check_winner = MagicMock(return_value=False)

        self.game_service.start_turn("player1")

        pod.update_score.assert_called_once_with(2)

    def test_fill_empty_space(self):
        pod = MagicMock()
        pod.player_id = "player1"
        self.game_service.controller.get_node_state = MagicMock(
            return_value={"tokyo-city": None, "tokyo-bay": None}
        )
        self.game_service.controller.relocate = MagicMock()
        self.game_service.num_players_alive = 5

        self.game_service.fill_empty_space(pod, 0)

        self.game_service.controller.relocate.assert_called_once_with(
            "player1", Location.OUTSIDE.value, Location.CITY.value
        )

    def test_slap_with_death_and_yield(self):
        pod1 = MagicMock()
        pod1.player_id = "player1"
        pod1.name = "Monster1"
        pod1.get_state.return_value = (10, 0, 0, "node1")

        pod2 = MagicMock()
        pod2.player_id = "player2"
        pod2.name = "Monster2"
        pod2.get_state.return_value = (1, 0, 0, "node2")  # low health

        pod3 = MagicMock()
        pod3.player_id = "player3"
        pod3.name = "Monster3"
        pod3.get_state.return_value = (10, 0, 0, "node3")

        self.game_service.players = {"player1": pod1, "player2": pod2, "player3": pod3}
        self.game_service.player_order = ["player1", "player2", "player3"]
        self.game_service.dead = set()
        self.game_service.locations = {
            "node1": Location.OUTSIDE,
            "node2": Location.CITY,
            "node3": Location.BAY,
        }
        self.game_service.is_in_tokyo = MagicMock(side_effect=[True, True, False])
        self.game_service.call_and_wait = MagicMock(return_value={"yield": True})
        self.game_service.controller.destroy_tokyo_bay = MagicMock(
            return_value={"playerId": "player3"}
        )
        self.game_service.controller.destroy_pod = MagicMock()
        self.game_service.controller.relocate = MagicMock()

        self.game_service.slap(pod1, "node1", 2)

        pod2.slap.assert_called_once_with(2)
        self.assertIn("player2", self.game_service.dead)
        self.game_service.controller.destroy_pod.assert_called_once_with(
            "player2", "node2"
        )

        pod3.slap.assert_called_once_with(2)
        self.game_service.call_and_wait.assert_called_once_with(
            MessageType.YIELD, "player3"
        )
        self.game_service.controller.relocate.assert_called_once_with(
            "player3", "node3", Location.OUTSIDE.value
        )

    @patch("game_service.service.game_service.roll_dices")
    def test_reroll_dices_keep_all(self, mock_roll_dices):
        pod = MagicMock()
        pod.player_id = "player1"
        pod.name = "Monster1"
        self.game_service.players = {"player1": pod}
        self.game_service.socketio.call.return_value = {
            "dicesToKeep": [1, 2, 3, 4, 5, 6]
        }
        mock_roll_dices.return_value = [1, 2, 3, 4, 5, 6]

        dices = self.game_service.reroll_dices(pod)

        self.assertEqual(len(dices), 6)
        self.assertEqual(self.game_service.socketio.call.call_count, 1)

    @patch("game_service.service.game_service.roll_dices")
    @patch("time.sleep")
    def test_decide_starter(self, mock_sleep, mock_roll_dices):
        self.game_service.player_order = ["player1", "player2"]
        player1_mock = MagicMock()
        player1_mock.get_state.return_value = (10, 0, 0, "node1")
        player2_mock = MagicMock()
        player2_mock.get_state.return_value = (10, 0, 0, "node2")
        self.game_service.players = {"player1": player1_mock, "player2": player2_mock}
        mock_roll_dices.side_effect = [
            [DiceSymbols.FIST.value],
            [DiceSymbols.FIST.value, DiceSymbols.FIST.value],
        ]
        starter_index = self.game_service.decide_starter()
        self.assertEqual(starter_index, 1)

    def test_notify_player_death(self):
        self.game_service.notify_player_death("player1")
        self.socketio.emit.assert_called_once_with("DEATH", {}, to="player1")

    def test_call_and_wait(self):
        self.game_service.call_and_wait("command", "player1", {"payload": "test"})
        self.socketio.call.assert_called_once_with(
            "command", {"payload": "test"}, to="player1", timeout=60
        )

    def test_game_loop_with_dead_player(self):
        self.game_service.start_game = MagicMock()
        self.game_service.decide_starter = MagicMock(return_value=0)
        self.game_service.start_turn = MagicMock()
        self.game_service.player_order = ["player1", "player2"]
        self.game_service.dead = {"player1"}
        player_mock = MagicMock()
        player_mock.get_state.return_value = (10, 0, 0, "node1")
        self.game_service.players = {"player1": player_mock, "player2": player_mock}
        self.game_service.controller.destroy_all = MagicMock()

        winner_pod = MagicMock()
        winner_pod.name = "player2"

        def set_winner(player_id):
            if player_id == "player2":
                self.game_service.winner = winner_pod

        self.game_service.start_turn.side_effect = set_winner
        self.game_service.game_loop()
        self.game_service.start_turn.assert_called_once_with("player2")

    def test_start_turn_winner(self):
        pod = MagicMock()
        pod.player_id = "player1"
        pod.get_state.return_value = (10, 20, 0, "node1")
        self.game_service.players = {"player1": pod}
        self.game_service.locations = {"node1": Location.CITY}
        self.game_service.is_in_tokyo = MagicMock(return_value=True)
        self.game_service.check_winner = MagicMock(return_value=True)
        self.game_service.reroll_dices = MagicMock()

        self.game_service.start_turn("player1")

        self.game_service.reroll_dices.assert_not_called()

    def test_start_turn_check_winner_after_dices(self):
        pod = MagicMock()
        pod.player_id = "player1"
        pod.get_state.return_value = (10, 0, 0, "node3")
        self.game_service.players = {"player1": pod}
        self.game_service.locations = {"node3": Location.OUTSIDE}
        self.game_service.is_in_tokyo = MagicMock(return_value=False)
        self.game_service.reroll_dices = MagicMock(return_value=[])
        self.game_service.resolve_dices = MagicMock()
        self.game_service.fill_empty_space = MagicMock(return_value=20)
        self.game_service.check_winner = MagicMock(side_effect=[False, True])

        self.game_service.start_turn("player1")

        self.assertEqual(self.game_service.check_winner.call_count, 2)

    def test_fill_empty_space_bay(self):
        pod = MagicMock()
        pod.player_id = "player1"
        self.game_service.controller.get_node_state = MagicMock(
            return_value={"tokyo-city": "player2", "tokyo-bay": None}
        )
        self.game_service.controller.relocate = MagicMock()
        self.game_service.num_players_alive = 5

        self.game_service.fill_empty_space(pod, 0)

        self.game_service.controller.relocate.assert_called_once_with(
            "player1", Location.OUTSIDE.value, Location.BAY.value
        )

    def test_slap_same_location(self):
        pod1 = MagicMock()
        pod1.player_id = "player1"
        pod1.name = "Monster1"
        pod1.get_state.return_value = (10, 0, 0, "node1")

        pod2 = MagicMock()
        pod2.player_id = "player2"
        pod2.name = "Monster2"
        pod2.get_state.return_value = (10, 0, 0, "node1")

        self.game_service.players = {"player1": pod1, "player2": pod2}
        self.game_service.player_order = ["player1", "player2"]
        self.game_service.dead = set()
        self.game_service.locations = {"node1": Location.CITY}

        self.game_service.slap(pod1, "node1", 2)

        pod2.slap.assert_not_called()

    @patch("game_service.service.game_service.roll_dices")
    @patch("time.sleep")
    def test_decide_starter_tie(self, mock_sleep, mock_roll_dices):
        self.game_service.player_order = ["player1", "player2"]
        player1_mock = MagicMock()
        player1_mock.get_state.return_value = (10, 0, 0, "node1")
        player2_mock = MagicMock()
        player2_mock.get_state.return_value = (10, 0, 0, "node2")
        self.game_service.players = {"player1": player1_mock, "player2": player2_mock}
        mock_roll_dices.side_effect = [
            [DiceSymbols.FIST.value],
            [DiceSymbols.FIST.value],
            [DiceSymbols.FIST.value],
            [DiceSymbols.FIST.value, DiceSymbols.FIST.value],
        ]
        starter_index = self.game_service.decide_starter()
        self.assertEqual(starter_index, 1)
