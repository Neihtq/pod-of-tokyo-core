from textual import on
from textual.app import ComposeResult
from textual.widgets import Button

from pod_of_tokyo_client.view.green_border_vertical import GreenBorderVertical
from pod_of_tokyo_commons.entities.dice_symbols import DiceSymbols

READY_BUTTON_ID = "ready-button"


class StartView(GreenBorderVertical):
    def compose(self) -> ComposeResult:
        self.focus_element = Button("Ready", id=READY_BUTTON_ID)
        yield self.focus_element

    def on_mount(self) -> None:
        self.focus_element.focus()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == READY_BUTTON_ID:
            event.button.disabled = True
            self.controller.confirm()

    def on_key(self, event) -> None:
        if event.key == "enter":
            event.button.disabled = True
            self.controller.confirm()
