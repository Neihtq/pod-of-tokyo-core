from textual.app import ComposeResult
from textual.widgets import Button, Input, Static

from pod_of_tokyo_client.view.green_border_vertical import GreenBorderVertical

ADDRESS_INPUT_ID = "address-input"
JOIN_LOBBY_BUTTON_ID = "join-lobby-button"


class JoinView(GreenBorderVertical):
    def compose(self) -> ComposeResult:
        yield Static("Enter address of Lobby")
        yield Input(id=ADDRESS_INPUT_ID)
        yield Button("Join Lobby", id=JOIN_LOBBY_BUTTON_ID)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == JOIN_LOBBY_BUTTON_ID:
            address_input = self.query_one(f"#{ADDRESS_INPUT_ID}")
            self.controller.join_lobby(address_input.value)
