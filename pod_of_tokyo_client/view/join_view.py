from textual import on
from textual.app import ComposeResult
from textual.widgets import Button, Input, Static

from pod_of_tokyo_client.view.green_border_vertical import GreenBorderVertical

ADDRESS_INPUT_ID = "address-input"
JOIN_LOBBY_BUTTON_ID = "join-lobby-button"


class JoinView(GreenBorderVertical):
    def compose(self) -> ComposeResult:
        yield Static("Enter address of Lobby")
        adress_input = Input(id=ADDRESS_INPUT_ID)
        self.focus_element = adress_input
        yield adress_input
        yield Button("Join Lobby", id=JOIN_LOBBY_BUTTON_ID)

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == JOIN_LOBBY_BUTTON_ID:
            self.join_lobby()

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.join_lobby()

    def join_lobby(self) -> None:
        address_input = self.query_one(f"#{ADDRESS_INPUT_ID}", Input)
        self.controller.join_lobby(address_input.value)

    def on_mount(self) -> None:
        self.focus_element.focus()
