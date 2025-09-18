from textual import on
from textual.app import ComposeResult
from textual.widgets import Button

from pod_of_tokyo_client.view.green_border_vertical import GreenBorderVertical

THROW_DICES_BUTTON_ID = "throws-dices-button"


class Phase1(GreenBorderVertical):
    def compose(self) -> ComposeResult:
        self.focus_element = Button("Throw Dices", id=THROW_DICES_BUTTON_ID)
        yield self.focus_element

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == THROW_DICES_BUTTON_ID:
            self.controller.throw_dices()

    def on_mount(self) -> None:
        self.focus_element.focus()
