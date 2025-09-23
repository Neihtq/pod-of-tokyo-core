from textual.containers import Horizontal
from textual.widgets import Static

from pod_of_tokyo_client.utils.constants import PLAYER_NAME_ID
from pod_of_tokyo_commons.constants import OUTSIDE_KEY, TOKYO_BAY_KEY, TOKYO_CITY_KEY
from pod_of_tokyo_commons.entities import Player
from pod_of_tokyo_commons.model import Location

stat_symbols = {
    "Health": ("♥", "heart"),
    "Score": ("★", "star"),
    "Energy": ("⚡", "thunder"),
}

locations = {
    TOKYO_CITY_KEY: Location.CITY,
    TOKYO_BAY_KEY: Location.BAY,
    OUTSIDE_KEY: Location.OUTSIDE,
}


def get_player_stats_widget(model):
    statics = [Static(model.player_name, id=PLAYER_NAME_ID)]
    for stat, value in model.player_stats.items():
        symbol, css_class = stat_symbols.get(stat, ("", None))
        static = Static(f"{stat} {symbol}: {value}", classes=css_class)
        statics.append(static)

    return statics


def get_game_state_widget(game_state):
    items = []
    for location_key, players in game_state.items():
        items.append(Static(locations[location_key].value, classes="location-key"))

        for p in players:
            player = Player(p)
            name_static = Static(f"{player.name}\t")
            name_health = Static(
                f"{stat_symbols["Health"][0]}{player.health}",
                classes=stat_symbols["Health"][1],
            )
            name_score = Static(
                f"{stat_symbols["Score"][0]}{player.score}",
                classes=stat_symbols["Score"][1],
            )
            name_energy = Static(
                f"{stat_symbols["Energy"][0]}{player.energy}",
                classes=stat_symbols["Energy"][1],
            )

            player_box = Horizontal(
                name_static, name_health, name_score, name_energy, classes="player-box"
            )
            items.append(player_box)
        items.append(Static(""))
    return items
