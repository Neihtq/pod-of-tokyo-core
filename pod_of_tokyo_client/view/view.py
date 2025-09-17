from textual.app import App, ComposeResult
from textual.containers import Grid, VerticalScroll
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from pod_of_tokyo_client.utils.constants import (
    EVENT_LOGS_BOX_ID,
    GAME_STATE_BOX_ID,
    MENU_BOX_ID,
    MENU_CONTENT_HEADER_ID,
    MENU_CONTENT_ID,
    PLAYER_STATS_BOX_ID,
)


class PodOfTokyoView(App):
    def __init__(self, model, controller):
        super().__init__()
        self.event_logs = []
        self.model = model
        self.controller = controller

    def compose(self):
        grid = Grid()
        grid.styles.grid_size_rows = 2
        grid.styles.grid_size_columns = 2

        with grid:
            player_stats = self.compose_box(title="Stats", id=PLAYER_STATS_BOX_ID)
            yield player_stats

            yield from self.compose_menu()

            event_logs = self.compose_box(title="Event Logs", id=EVENT_LOGS_BOX_ID)
            yield event_logs
            ai_chat = self.compose_box(title="Game State", id=GAME_STATE_BOX_ID)
            yield ai_chat

    def compose_box(self, title, id):
        static = Static(id=id)
        static.border_title = title
        static.styles.border = ("solid", "green")
        static.styles.width = "1fr"
        static.styles.height = "1fr"
        return static

    def compose_menu(self) -> ComposeResult:
        menu_options = [
            Option("Option A", "A"),
            Option("Option B", "B"),
            Option("Option C", "C"),
            Option("Option D", "D"),
        ]
        menu_box = VerticalScroll(id=MENU_BOX_ID)
        menu_box.styles.border = ("solid", "green")
        menu_box.border_title = "Menu"
        menu_box.styles.width = "1fr"
        menu_box.styles.height = "1fr"
        with menu_box:
            yield Static("Choose on option", id=MENU_CONTENT_HEADER_ID)
            yield OptionList(*menu_options, id=MENU_CONTENT_ID)

    def on_mount(self) -> None:
        menu_list = self.query_one(f"#{MENU_CONTENT_ID}")
        menu_list.focus()

    def set_player_stats(self, health, score, energy):
        stats = f"""
        Health: {health}
        Score: {score}
        Energy: {energy}
        """

        player_stats = self.query_one(f"#{PLAYER_STATS_BOX_ID}")
        player_stats.update(stats)
