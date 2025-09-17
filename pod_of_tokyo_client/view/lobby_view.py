from textual import on
from textual.app import ComposeResult
from textual.widgets import Button, Label, ListItem, ListView, Static

from pod_of_tokyo_client.view.green_border_vertical import GreenBorderVertical

START_GAME_BUTTON_ID = "start-game-button"


class LobbyView(GreenBorderVertical):
    def compose(self) -> ComposeResult:
        yield Static("Lobby")

        players = [ListItem(Label(player)) for player in self.model.players]
        list_view = ListView(*players)
        self.focus_element = list_view
        yield list_view
        yield Button("Start Game", id=START_GAME_BUTTON_ID, disabled=len(players) >= 2)

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == START_GAME_BUTTON_ID:
            self.controller.start_game()

    def on_key(self, event) -> None:
        if event.key == "enter":
            self.controller.start_game()

    def on_mount(self) -> None:
        self.focus_element.focus()
