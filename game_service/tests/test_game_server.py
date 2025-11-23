import unittest
from unittest.mock import patch

from game_service.game_server import GameServer


class TestGameServer(unittest.TestCase):
    def setUp(self):
        with patch("game_service.game_server.GameService"):
            self.game_server = GameServer()
            self.socketio = self.game_server.socketio
            self.app = self.game_server.app
            self.game_service = self.game_server.game_service

    def test_on_connect(self):
        client = self.socketio.test_client(self.app)
        self.assertTrue(client.is_connected())
        self.assertEqual(len(self.game_server.connections), 1)
        client.disconnect()

    def test_on_disconnect(self):
        client = self.socketio.test_client(self.app)
        self.assertTrue(client.is_connected())
        self.assertEqual(len(self.game_server.connections), 1)
        client.disconnect()
        self.assertEqual(len(self.game_server.connections), 0)
        self.game_service.remove.assert_called_once()

    def test_handle_get_name(self):
        client = self.socketio.test_client(self.app)
        response = client.emit("get_name", callback=True)
        self.assertIn("playerName", response)

    def test_handle_start_game(self):
        client = self.socketio.test_client(self.app)
        client.emit("start_game")
        self.game_service.set_players.assert_called_with(self.game_server.connections)
        self.game_service.game_loop.assert_called_once()

    def test_notify_all(self):
        with patch.object(self.socketio, "emit") as mock_emit:
            self.game_server.notify_all()
            mock_emit.assert_called_once()

    def test_on_connect_no_monster_names(self):
        self.game_server.monster_names = []
        client = self.socketio.test_client(self.app)
        self.assertEqual(len(self.game_server.connections), 0)

    def test_run(self):
        with patch.object(self.socketio, "run") as mock_run:
            self.game_server.run()
            mock_run.assert_called_with(self.app, host=self.game_server.host, port=self.game_server.port)
