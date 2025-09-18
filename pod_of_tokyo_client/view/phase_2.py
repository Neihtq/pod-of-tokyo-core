from textual import on
from textual.app import ComposeResult
from textual.widgets import Button, SelectionList, Static

from pod_of_tokyo_client.view.green_border_vertical import GreenBorderVertical

CONFIRM_BUTTON_ID = "confirm-button"


class Phase2(GreenBorderVertical):
    def compose(self) -> ComposeResult:
        yield Static("Select dices to keep")

        dices = [(dice, i) for i, dice in enumerate(self.model.dices)]
        dices_list = SelectionList(*dices)
        dices_list.styles.max_height = 10
        self.focus_element = dices_list
        yield dices_list
        yield Button("Confirm", id=CONFIRM_BUTTON_ID)

    def on_mount(self) -> None:
        self.focus_element.focus()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == CONFIRM_BUTTON_ID:
            self.controller.resolve_dices()
