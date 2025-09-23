from textual.app import App
from textual.containers import Container, Grid, Vertical, VerticalScroll
from textual.widgets import Static

from pod_of_tokyo_client.utils.compose_stats import (
    get_game_state_widget,
    get_player_stats_widget,
)
from pod_of_tokyo_client.utils.constants import (
    EVENT_LOGS_BOX_ID,
    GAME_STATE_BOX_ID,
    MENU_BOX_ID,
    MENU_CONTENT_ID,
    PLAYER_STATS_BOX_ID,
)
from pod_of_tokyo_client.view.player_menus import JoinView


class PodOfTokyoView(App):
    CSS_PATH = "css/green_border.tcss"

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
            player_stats_container = Container(
                Static("Stats"), id=PLAYER_STATS_BOX_ID, classes="container"
            )
            player_stats_container.border_title = "Stats"
            yield player_stats_container

            join_view = JoinView(self.model, self.controller, id=MENU_CONTENT_ID)
            join_view_container = Container(
                join_view, id=MENU_BOX_ID, classes="container"
            )
            join_view_container.border_title = "Menu"
            yield join_view_container

            event_logs = VerticalScroll(id=EVENT_LOGS_BOX_ID, classes="container")
            event_logs.border_title = "Event Logs"
            yield event_logs

            game_state = Container(Static(), id=GAME_STATE_BOX_ID, classes="container")
            game_state.border_title = "Game State"
            yield game_state

    def add_event(self, event):
        event_container = self.query_one(f"#{EVENT_LOGS_BOX_ID}", VerticalScroll)
        new_message_static = Static(event)
        new_message_static.styles.border = ("solid", "grey")
        event_container.mount(new_message_static)
        event_container.scroll_end(animate=False)

    def compose_player_stats(self):
        player_stats_container = self.query_one(f"#{PLAYER_STATS_BOX_ID}")
        player_stats_container.remove_children()
        statics = get_player_stats_widget(self.model)
        player_stats_container.mount(Vertical(*statics))

    def compose_game_state(self):
        game_state_container = self.query_one(f"#{GAME_STATE_BOX_ID}", Container)
        game_state_container.remove_children()

        game_state_items = get_game_state_widget(self.model.game_state)
        game_state_list = Vertical(*game_state_items, classes="game-state-list")
        game_state_container.mount(game_state_list)

    def compose_box(self, title):
        static = Static()
        static.border_title = title
        return static

    def compose_menu(self, view_class):
        content = view_class(model=self.model, controller=self.controller)
        menu_container = self.query_one(f"#{MENU_BOX_ID}")
        menu_container.remove_children()
        menu_container.mount(content)

    def on_mount(self) -> None:
        self.compose_player_stats()
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
