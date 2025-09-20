from pod_of_tokyo_commons.entities.game_state import GameState
from pod_of_tokyo_commons.entities.player import Player
from pod_of_tokyo_commons.model.update_event import UpdateEvent


class Message:
    def __init__(self, data):
        self.message = data.get("message", None)
        self.dices = data.get("dices")

        update = data.get("update", None)
        if update:
            self.player_update = UpdateEvent(update)

        game_state_dict = data.get("gameState", None)
        if game_state_dict:
            game_state = {
                k: [Player(player) for player in game_state_dict[k]]
                for k in game_state_dict
            }
            self.game_state = GameState(game_state)
