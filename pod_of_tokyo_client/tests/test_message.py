import unittest

from pod_of_tokyo_client.middleware.message import Message


class TestMessage(unittest.TestCase):
    def test_message_with_members(self):
        data = {"members": ["player1", "player2"]}
        message = Message(data)
        self.assertEqual(message.members, ["player1", "player2"])

    def test_message_with_message(self):
        data = {"message": "Test message"}
        message = Message(data)
        self.assertEqual(message.message, "Test message")

    def test_message_with_dices(self):
        data = {"dices": [1, 2, 3]}
        message = Message(data)
        self.assertEqual(message.dices, [1, 2, 3])

    def test_message_with_update(self):
        update_data = {
            "health": 1,
            "damage": 2,
            "energy": 3,
            "location": "Tokyo",
            "score": 4,
        }
        data = {"update": update_data}
        message = Message(data)
        self.assertEqual(message.player_update.health, 1)
        self.assertEqual(message.player_update.damage, 2)
        self.assertEqual(message.player_update.energy, 3)
        self.assertEqual(message.player_update.location, "Tokyo")
        self.assertEqual(message.player_update.score, 4)

    def test_message_with_game_state(self):
        game_state_data = {
            "tokyo-city": [
                {"health": 10, "score": 0, "energy": 0, "location": "tokyo-city"}
            ],
            "tokyo-bay": [],
            "outside": [],
        }
        data = {"gameState": game_state_data}
        message = Message(data)
        self.assertIsNotNone(message.game_state)
        self.assertIsNotNone(message.game_state.players_in_city)
