from pod_of_tokyo_commons.constants import OUTSIDE_KEY, TOKYO_BAY_KEY, TOKYO_CITY_KEY


class GameState:
    def __init__(self, game_state):
        self.players_in_city = game_state[TOKYO_CITY_KEY]
        self.players_in_bay = game_state[TOKYO_BAY_KEY]
        self.players_in_outside = game_state[OUTSIDE_KEY]
