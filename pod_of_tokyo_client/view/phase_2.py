from textual import on
from textual.app import ComposeResult
from textual.widgets import Select, SelectionList, Static

from pod_of_tokyo_client.view.green_border_vertical import GreenBorderVertical


class Phase2(GreenBorderVertical):
    def compose(self) -> ComposeResult:
        yield Static("Select dices to keep")

        dices = [(dice, i) for i, dice in enumerate(self.model.dices)]
        dices_list = SelectionList(*dices)
        self.focus_element = dices_list
        yield dices_list

    def on_mount(self) -> None:
        self.focus_element.focus()
