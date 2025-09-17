from textual.app import ComposeResult
from textual.widgets import Static

from pod_of_tokyo_client.view.green_border_vertical import GreenBorderVertical
from pod_of_tokyo_commons.entities.dice_symbols import DiceSymbols


class StartView(GreenBorderVertical):
    def compose(self) -> ComposeResult:
        yield Static(f"{self.count_fists()} {DiceSymbols.FIST.value}/s")

    def count_fists(self) -> int:
        counter = 0
        for dice in self.model.dices:
            if dice == DiceSymbols.FIST.value:
                counter += 1

        return counter
