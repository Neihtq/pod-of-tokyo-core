from textual import on
from textual.app import ComposeResult
from textual.widgets import Static

from pod_of_tokyo_client.view.green_border_vertical import GreenBorderVertical

READY_BUTTON_ID = "ready-button"


class DisabledView(GreenBorderVertical):
    def compose(self) -> ComposeResult:
        message = "It's not your turn. Please pay attention to the event logs in the bottom left."
        if not self.model.alive:
            message = "You died."
        yield Static(message)
