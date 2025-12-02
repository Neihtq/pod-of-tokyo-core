import unittest
from unittest.mock import MagicMock, call, patch

from pod_of_tokyo_commons.constants import OUTSIDE_KEY, TOKYO_BAY_KEY, TOKYO_CITY_KEY
from pod_of_tokyo_commons.entities import DiceSymbols
from pod_of_tokyo_commons.model import Location, MessageType, PodStatus

from game_service.service.game_service import GameService
from game_service.service.player_manager import PlayerManager


class TestGameService(unittest.TestCase):
    def setUp(self):
        self.mock_socketio = MagicMock()
        self.controller_url = "http://controller:8080"

        with patch(
            "game_service.service.game_service.ControllerClient"
        ) as MockController:
            self.game_service = GameService(self.mock_socketio, self.controller_url)
            self.mock_controller = self.game_service.controller

        self.game_service.manager = MagicMock()
        self.game_service.notifier = MagicMock()
        self.game_service.locations = {
            TOKYO_CITY_KEY: Location.CITY,
            TOKYO_BAY_KEY: Location.BAY,
            OUTSIDE_KEY: Location.OUTSIDE,
        }
        self.game_service.tokyo_bay_destroyed = False

    def test_start_game(self):
        players = [{"playerId": "p1", "name": "P1", "podUrl": "url1"}]
        self.game_service.manager.get_player_list.return_value = players
        self.mock_controller.init_game.return_value = {
            "players": players,
            "locations": [TOKYO_CITY_KEY, TOKYO_BAY_KEY, OUTSIDE_KEY],
        }
        self.game_service.manager.get_num_alive.return_value = 1

        with patch.object(self.game_service, "wait_for_game_ready"):
            self.game_service.start_game()

        self.game_service.notifier.notify_all.assert_any_call("Initializing game...")
        self.mock_controller.init_game.assert_called_with(players)
        self.game_service.manager.set_pod_and_add_to_order.assert_called()
        self.game_service.notifier.notify_game_start.assert_called()
        self.game_service.notifier.notify_all.assert_any_call("Game started!")

    def test_start_turn_in_tokyo_gets_points(self):
        player_id = "p1"
        mock_pod = MagicMock()
        mock_pod.player_id = player_id
        mock_pod.name = "P1"

        mock_pod.get_state.return_value = (10, 0, 0, TOKYO_CITY_KEY)
        self.game_service.manager.get_pod.return_value = mock_pod

        self.game_service.check_winner = MagicMock(return_value=False)
        self.game_service.reroll_dices = MagicMock(return_value=[])
        self.game_service.resolve_dices = MagicMock()

        self.game_service.start_turn(player_id)

        mock_pod.update_score.assert_called_with(2)
        self.game_service.notifier.notify_all.assert_any_call("P1 received 2 stars!")

    def test_start_turn_outside_enters_tokyo_if_empty(self):
        player_id = "p1"
        mock_pod = MagicMock()
        mock_pod.player_id = player_id
        mock_pod.name = "P1"
        mock_pod.get_state.return_value = (10, 0, 0, OUTSIDE_KEY)
        self.game_service.manager.get_pod.return_value = mock_pod

        self.mock_controller.get_node_state.return_value = {TOKYO_CITY_KEY: None}

        self.game_service.check_winner = MagicMock(return_value=False)
        self.game_service.reroll_dices = MagicMock(return_value=[])
        self.game_service.resolve_dices = MagicMock()

        self.game_service.start_turn(player_id)

        self.mock_controller.relocate.assert_called_with(
            player_id, OUTSIDE_KEY, TOKYO_CITY_KEY
        )
        mock_pod.update_score.assert_called_with(1)

    def test_resolve_dices_heal(self):
        mock_pod = MagicMock()
        mock_pod.name = "P1"
        dices = [DiceSymbols.HEART.value] * 3
        location = Location.OUTSIDE

        with patch.object(self.game_service, "heal_player") as mock_heal:
            self.game_service.resolve_dices(mock_pod, dices, location)
            mock_heal.assert_called_with(mock_pod, 3, location)

    def test_resolve_dices_slap(self):
        mock_pod = MagicMock()
        mock_pod.name = "P1"
        dices = [DiceSymbols.FIST.value] * 2
        location = Location.CITY

        with patch.object(self.game_service, "slap") as mock_slap:
            self.game_service.resolve_dices(mock_pod, dices, location)
            mock_slap.assert_called_with(mock_pod, location, damage=2)

    def test_resolve_dices_energy(self):
        mock_pod = MagicMock()
        mock_pod.name = "P1"
        dices = [DiceSymbols.THUNDER.value] * 4
        location = Location.OUTSIDE

        self.game_service.resolve_dices(mock_pod, dices, location)
        mock_pod.charge_energy.assert_called_with(energy=4)

    def test_resolve_dices_points(self):
        mock_pod = MagicMock()
        mock_pod.name = "P1"

        dices = ["1", "1", "1"]
        location = Location.OUTSIDE

        self.game_service.resolve_dices(mock_pod, dices, location)
        mock_pod.update_score.assert_called_with(score=1)

    def test_heal_player_outside(self):
        mock_pod = MagicMock()
        mock_pod.name = "P1"
        mock_pod.get_state.return_value = (5, 0, 0, OUTSIDE_KEY)

        self.game_service.heal_player(mock_pod, 3, Location.OUTSIDE)

        mock_pod.heal.assert_called_with(health=3)

    def test_heal_player_in_tokyo_fails(self):
        mock_pod = MagicMock()
        mock_pod.name = "P1"

        self.game_service.heal_player(mock_pod, 3, Location.CITY)

        mock_pod.heal.assert_not_called()
        self.game_service.notifier.notify_all.assert_called_with(
            "P1 is in Tokyo! Healing in Tokyo is not possible!"
        )

    def test_check_winner_by_score(self):
        mock_pod = MagicMock()
        mock_pod.name = "P1"
        score = 20

        is_winner = self.game_service.check_winner(mock_pod, score)

        self.assertTrue(is_winner)
        self.assertEqual(self.game_service.winner, "P1")

    def test_check_winner_by_elimination(self):
        mock_pod = MagicMock()
        mock_pod.name = "P1"
        mock_pod.player_id = "p1"
        score = 10

        self.game_service.manager.get_num_alive.return_value = 1
        self.game_service.manager.is_dead.return_value = False

        is_winner = self.game_service.check_winner(mock_pod, score)

        self.assertTrue(is_winner)
        self.assertEqual(self.game_service.winner, "P1")

    def test_reroll_dices(self):
        mock_pod = MagicMock()
        mock_pod.name = "P1"
        mock_pod.player_id = "p1"

        with patch("game_service.service.game_service.roll_dices") as mock_roll:
            mock_roll.side_effect = [
                ["1", "1", "2", "2", "3", "3"],
                ["P", "P", "H", "H"],
                ["E", "E"],
            ]

            self.game_service.notifier.call_and_wait.side_effect = [
                None,
                {"dices": ["1", "1"]},
                {"dices": ["P", "P"]},
                {"dices": ["E", "E"]},
            ]

            final_dices = self.game_service.reroll_dices(mock_pod)

            self.assertEqual(len(final_dices), 6)
            self.assertCountEqual(final_dices, ["1", "1", "P", "P", "E", "E"])

    def test_slap_turn_zero(self):
        mock_pod = MagicMock()
        self.game_service.turn = 0

        self.game_service.slap(mock_pod, Location.CITY, 1)

        self.game_service.notifier.notify_all.assert_called_with(
            "The beginning player cannot slap other players on their first turn!"
        )

    def test_slap_damages_others(self):
        self.game_service.turn = 1
        active_pod = MagicMock()
        active_pod.player_id = "p1"
        active_pod.name = "P1"

        target_pod = MagicMock()
        target_pod.player_id = "p2"
        target_pod.name = "P2"
        target_pod.get_state.return_value = (10, 0, 0, OUTSIDE_KEY)

        self.game_service.manager.get_player_order.return_value = ["p1", "p2"]
        self.game_service.manager.is_dead.return_value = False
        self.game_service.manager.get_pod.return_value = target_pod

        self.game_service.slap(active_pod, Location.CITY, 2)

        target_pod.slap.assert_called_with(2)
        self.game_service.notifier.notify_all.assert_any_call(
            "P1 slapped P2! P2 lost 2 life points."
        )

    def test_slap_kills_player(self):
        self.game_service.turn = 1
        active_pod = MagicMock()
        active_pod.player_id = "p1"
        active_pod.name = "P1"

        target_pod = MagicMock()
        target_pod.player_id = "p2"
        target_pod.name = "P2"
        target_pod.get_state.return_value = (2, 0, 0, OUTSIDE_KEY)

        self.game_service.manager.get_player_order.return_value = ["p1", "p2"]
        self.game_service.manager.is_dead.return_value = False
        self.game_service.manager.get_pod.return_value = target_pod
        self.game_service.manager.get_num_alive.return_value = 2

        self.game_service.slap(active_pod, Location.CITY, 2)

        target_pod.slap.assert_called_with(2)
        self.game_service.manager.add_dead_player.assert_called_with("p2")
        self.mock_controller.destroy_pod.assert_called_with("p2", OUTSIDE_KEY)
        self.game_service.notifier.notify_death.assert_called_with("p2")

    def test_slap_yield_tokyo(self):
        self.game_service.turn = 1
        active_pod = MagicMock()
        active_pod.player_id = "p1"
        active_pod.name = "P1"

        target_pod = MagicMock()
        target_pod.player_id = "p2"
        target_pod.name = "P2"
        target_pod.get_state.return_value = (10, 0, 0, TOKYO_CITY_KEY)

        self.game_service.manager.get_player_order.return_value = ["p1", "p2"]
        self.game_service.manager.is_dead.return_value = False
        self.game_service.manager.get_pod.return_value = target_pod

        self.game_service.notifier.call_and_wait.return_value = {"isYielding": True}

        self.game_service.slap(active_pod, Location.OUTSIDE, 1)

        self.mock_controller.relocate.assert_called_with(
            "p2", TOKYO_CITY_KEY, OUTSIDE_KEY
        )
        self.game_service.notifier.notify_all.assert_any_call("P2 is leaving Tokyo!")

    def test_decide_starter(self):
        self.game_service.manager.get_player_order.return_value = ["p1", "p2"]

        with patch("game_service.service.game_service.roll_dices") as mock_roll:
            mock_roll.side_effect = [
                [DiceSymbols.FIST.value],
                [DiceSymbols.FIST.value, DiceSymbols.FIST.value],
            ]

            self.game_service.manager.get_player_index.return_value = 1

            starter_index = self.game_service.decide_starter()

            self.assertEqual(starter_index, 1)

    def test_destroy_tokyo_bay(self):
        self.mock_controller.destroy_tokyo_bay.return_value = {"playerId": "p3"}
        self.game_service.manager.get_pod.return_value.name = "P3"

        self.game_service.destroy_tokyo_bay()

        self.assertTrue(self.game_service.tokyo_bay_destroyed)
        self.game_service.notifier.notify_all.assert_any_call(
            "Tokyo Bay has been flooded!"
        )
        self.game_service.notifier.notify_all.assert_any_call("P3 is leaving Tokyo!")

    def test_fill_empty_space_bay(self):
        mock_pod = MagicMock()
        mock_pod.player_id = "p1"
        mock_pod.name = "P1"

        self.mock_controller.get_node_state.return_value = {
            TOKYO_CITY_KEY: "p2",
            TOKYO_BAY_KEY: None,
        }
        self.game_service.manager.get_num_alive.return_value = 5

        score, location_key = self.game_service.fill_empty_space(mock_pod, 0)

        self.assertEqual(location_key, TOKYO_BAY_KEY)
        self.mock_controller.relocate.assert_called_with(
            "p1", OUTSIDE_KEY, TOKYO_BAY_KEY
        )

    def test_remove(self):
        self.game_service.remove("sid")
        self.game_service.manager.remove_player.assert_called_with("sid")

    def test_init_notifier(self):
        self.game_service.init_notifier()
        self.assertIsNotNone(self.game_service.notifier)

    def test_wait_for_game_ready(self):

        self.mock_controller.get_fleet_status.side_effect = [
            [PodStatus.INACTIVE.value],
            [PodStatus.ACTIVE.value],
        ]

        with patch("time.sleep") as mock_sleep:
            self.game_service.wait_for_game_ready()
            self.assertEqual(mock_sleep.call_count, 2)

    def test_check_winner_no_winner(self):
        mock_pod = MagicMock()
        mock_pod.name = "P1"
        mock_pod.player_id = "p1"
        score = 10

        self.game_service.manager.get_num_alive.return_value = 2

        is_winner = self.game_service.check_winner(mock_pod, score)

        self.assertFalse(is_winner)
        self.assertIsNone(self.game_service.winner)

    def test_start_turn_fill_empty_space(self):
        player_id = "p1"
        mock_pod = MagicMock()
        mock_pod.player_id = player_id
        mock_pod.name = "P1"
        mock_pod.get_state.return_value = (10, 0, 0, OUTSIDE_KEY)
        self.game_service.manager.get_pod.return_value = mock_pod

        with patch.object(self.game_service, "fill_empty_space") as mock_fill:
            mock_fill.return_value = (1, TOKYO_CITY_KEY)
            self.game_service.locations[TOKYO_CITY_KEY] = Location.CITY

            self.game_service.check_winner = MagicMock(return_value=False)
            self.game_service.reroll_dices = MagicMock(return_value=[])
            self.game_service.resolve_dices = MagicMock()

            self.game_service.start_turn(player_id)

            self.assertEqual(mock_fill.call_count, 1)

    def test_reroll_dices_keeps_remaining(self):
        mock_pod = MagicMock()
        mock_pod.name = "P1"
        mock_pod.player_id = "p1"

        with patch("game_service.service.game_service.roll_dices") as mock_roll:
            mock_roll.return_value = ["1", "1", "1", "1", "1", "1"]

            self.game_service.notifier.call_and_wait.return_value = {"dices": []}

            final_dices = self.game_service.reroll_dices(mock_pod)

            self.assertEqual(len(final_dices), 6)
            self.assertEqual(final_dices, ["1", "1", "1", "1", "1", "1"])

    def test_slap_skips(self):
        self.game_service.turn = 1
        active_pod = MagicMock()
        active_pod.player_id = "p1"

        target_pod = MagicMock()
        target_pod.player_id = "p2"

        self.game_service.manager.get_player_order.return_value = ["p1", "p2"]
        self.game_service.manager.is_dead.side_effect = lambda pid: pid == "p2"

        self.game_service.slap(active_pod, Location.CITY, 1)

        target_pod.slap.assert_not_called()

    def test_decide_starter_tie_break(self):
        self.game_service.manager.get_player_order.return_value = ["p1", "p2"]

        with patch("game_service.service.game_service.roll_dices") as mock_roll:
            mock_roll.side_effect = [
                [DiceSymbols.FIST.value],
                [DiceSymbols.FIST.value],
                [DiceSymbols.FIST.value],
                [DiceSymbols.FIST.value, DiceSymbols.FIST.value],
            ]

            self.game_service.manager.get_player_index.return_value = 1

            starter_index = self.game_service.decide_starter()

            self.assertEqual(starter_index, 1)

    def test_set_players(self):
        name_by_id = {"p1": "P1"}
        self.game_service.set_players(name_by_id)
        self.assertIsInstance(self.game_service.manager, PlayerManager)

    def test_start_turn_calls_resolve_dices(self):
        player_id = "p1"
        mock_pod = MagicMock()
        mock_pod.player_id = player_id
        mock_pod.name = "P1"
        mock_pod.get_state.return_value = (10, 0, 0, OUTSIDE_KEY)
        self.game_service.manager.get_pod.return_value = mock_pod
        self.game_service.manager.get_num_alive.return_value = 2

        self.game_service.check_winner = MagicMock(return_value=False)
        self.game_service.reroll_dices = MagicMock(return_value=[])
        self.game_service.resolve_dices = MagicMock()

        self.game_service.fill_empty_space = MagicMock(return_value=(0, None))

        self.game_service.start_turn(player_id)

        self.game_service.resolve_dices.assert_called()

    def test_slap_attacker_and_target_in_tokyo(self):
        self.game_service.turn = 1
        active_pod = MagicMock()
        active_pod.player_id = "p1"
        active_pod.name = "P1"

        target_pod = MagicMock()
        target_pod.player_id = "p2"
        target_pod.name = "P2"
        target_pod.get_state.return_value = (10, 0, 0, TOKYO_CITY_KEY)

        self.game_service.manager.get_player_order.return_value = ["p1", "p2"]
        self.game_service.manager.is_dead.return_value = False
        self.game_service.manager.get_pod.return_value = target_pod

        self.game_service.manager.get_pod.return_value = target_pod

        with patch(
            "game_service.service.game_service.game_utils.is_in_tokyo"
        ) as mock_is_in_tokyo:
            mock_is_in_tokyo.return_value = True

            self.game_service.slap(active_pod, Location.BAY, 1)

            target_pod.slap.assert_not_called()
