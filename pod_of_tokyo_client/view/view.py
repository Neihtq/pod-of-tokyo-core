from textual.app import App
from textual.containers import Container, Grid, VerticalScroll
from textual.widgets import Static

from pod_of_tokyo_client.utils.constants import (
    EVENT_LOGS_BOX_ID,
    GAME_STATE_BOX_ID,
    MENU_BOX_ID,
    MENU_CONTENT_ID,
    PLAYER_STATS_BOX_ID,
)
from pod_of_tokyo_client.view.join_view import JoinView


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

            join_view = JoinView(self.model, self.controller, id=MENU_CONTENT_ID)
            yield Container(join_view, id=MENU_BOX_ID)

            event_logs = VerticalScroll(id=EVENT_LOGS_BOX_ID)
            event_logs.border_title = "Event Logs"
            event_logs.styles.border = ("solid", "green")
            event_logs.styles.width = "1fr"
            event_logs.styles.height = "1fr"
            yield event_logs

            ai_chat = self.compose_box(title="Game State", id=GAME_STATE_BOX_ID)
            yield ai_chat

    def add_event(self, event):
        event_container = self.query_one(f"#{EVENT_LOGS_BOX_ID}", VerticalScroll)
        new_message_static = Static(event)
        new_message_static.styles.border = ("solid", "grey")
        event_container.mount(new_message_static)
        event_container.scroll_end(animate=False)

    def compose_box(self, title, id):
        static = Static(id=id)
        static.border_title = title
        static.styles.border = ("solid", "green")
        static.styles.width = "1fr"
        static.styles.height = "1fr"
        return static

    def compose_menu(self, view_class):
        content = view_class(model=self.model, controller=self.controller)
        menu_container = self.query_one(f"#{MENU_BOX_ID}")
        menu_container.remove_children()
        menu_container.mount(content)

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
