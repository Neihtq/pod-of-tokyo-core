import unittest
from unittest.mock import MagicMock, patch, call
from game_service.service.notification_service import NotificationService
from pod_of_tokyo_commons.model import MessageType
from pod_of_tokyo_commons.constants import TOKYO_CITY_KEY, OUTSIDE_KEY

class TestNotificationService(unittest.TestCase):
    def setUp(self):
        self.mock_sio = MagicMock()
        self.mock_manager = MagicMock()
        self.service = NotificationService(self.mock_sio, self.mock_manager)

    def test_call_and_wait(self):
        expected_response = {"data": "test"}
        self.mock_sio.call.return_value = {"response": expected_response}
        
        response = self.service.call_and_wait(MessageType.ROLL, "p1", {"foo": "bar"})
        
        self.mock_sio.call.assert_called_with(
            MessageType.ROLL.value, 
            {"foo": "bar"}, 
            to="p1", 
            timeout=600
        )
        self.assertEqual(response, expected_response)

    def test_notify_all(self):
        # Mock get_game_state via manager
        self.mock_manager.player_order = ["p1"]
        self.mock_manager.is_dead.return_value = False
        mock_pod = MagicMock()
        mock_pod.name = "P1"
        # health, score, energy, location
        mock_pod.get_state.return_value = (10, 0, 0, OUTSIDE_KEY)
        self.mock_manager.get_pod.return_value = mock_pod
        
        with patch("time.sleep") as mock_sleep:
            self.service.notify_all("Hello")
            
            self.mock_sio.emit.assert_called()
            args, kwargs = self.mock_sio.emit.call_args
            self.assertEqual(args[0], MessageType.EVENT.value)
            self.assertEqual(kwargs['to'], "king-of-tokyo") # ROOM constant is "king-of-tokyo"
            self.assertEqual(args[1]['message'], "Hello")
            self.assertIn("gameState", args[1])
            
            mock_sleep.assert_called_with(1.0)

    def test_notify_death(self):
        self.service.notify_death("p1")
        self.mock_sio.emit.assert_called_with(
            MessageType.DEATH.value, 
            {}, 
            to="p1"
        )

    def test_send_player_update(self):
        mock_update = MagicMock()
        mock_update.to_dict.return_value = {"health": 9}
        
        self.service.send_player_update(mock_update, "p1")
        
        self.mock_sio.emit.assert_called_with(
            MessageType.UPDATE.value, 
            {"update": {"health": 9}}, 
            to="p1"
        )

    def test_notify_game_start(self):
        self.service.notify_game_start()
        self.mock_sio.emit.assert_called_with(
            MessageType.START_GAME.value, 
            {}, 
            to="king-of-tokyo"
        )

    def test_notify_turn_end(self):
        self.service.notify_turn_end("p1")
        self.mock_sio.emit.assert_called_with(
            MessageType.END_TURN.value, 
            {}, 
            to="p1"
        )

    def test_notify_game_end(self):
        self.service.notify_game_end("Winner")
        self.mock_sio.emit.assert_called_with(
            MessageType.END_GAME.value, 
            {"winner": "Winner"}, 
            to="king-of-tokyo"
        )

    def test_get_game_state(self):
        self.mock_manager.player_order = ["p1", "p2"]
        # p2 is dead
        self.mock_manager.is_dead.side_effect = lambda pid: pid == "p2"
        
        mock_pod = MagicMock()
        mock_pod.name = "P1"
        mock_pod.get_state.return_value = (10, 5, 2, TOKYO_CITY_KEY)
        self.mock_manager.get_pod.return_value = mock_pod
        
        game_state = self.service.get_game_state()
        
        state_dict = game_state.to_dict()
        self.assertIn(TOKYO_CITY_KEY, state_dict)
        self.assertEqual(len(state_dict[TOKYO_CITY_KEY]), 1)
        player_data = state_dict[TOKYO_CITY_KEY][0]
        self.assertEqual(player_data['name'], "P1")
        self.assertEqual(player_data['health'], 10)
