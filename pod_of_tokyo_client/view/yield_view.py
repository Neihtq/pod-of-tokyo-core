from textual import on
from textual.app import ComposeResult
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from pod_of_tokyo_client.view.green_border_vertical import GreenBorderVertical

YIELD_OPTION_LIST_ID = "yield-option-list"


class YieldView(GreenBorderVertical):
    def compose(self) -> ComposeResult:
        yield Static("You've got slapped! Will you yield?")

        option_list = OptionList(Option("Yes"), Option("No"), id=YIELD_OPTION_LIST_ID)
        self.focus_element = option_list
        yield option_list

    def on_mount(self) -> None:
        self.focus_element.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        selected_value = event.option.prompt
        print(selected_value)
        self.controller.is_yielding(selected_value == "yes")
