from textual.app import ComposeResult
from textual.widgets import Static

from pod_of_tokyo_client.view.green_border_vertical import GreenBorderVertical

WINNER_LABEL_ID = "winner-label"
LOSER_LABEL_ID = "loser-label"


class EndGameView(GreenBorderVertical):
    def compose(self) -> ComposeResult:
        message = "You are the king of Tokyo!"
        static_id = WINNER_LABEL_ID
        if not self.model.is_winner:
            message = f"{self.model.winner} is the king of Tokyo."
            static_id = LOSER_LABEL_ID

        yield Static(message, id=static_id)
