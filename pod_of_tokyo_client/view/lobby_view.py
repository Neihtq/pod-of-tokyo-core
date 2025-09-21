from textual import on
from textual.app import ComposeResult
from textual.widgets import Button, Label, ListItem, ListView, Static

from pod_of_tokyo_client.view.green_border_vertical import GreenBorderVertical

START_GAME_BUTTON_ID = "start-game-button"
PLAYER_LIST_ID = "player-list"


class LobbyView(GreenBorderVertical):
    def compose(self) -> ComposeResult:
        yield Static("Lobby")

        players = self.create_player_list()
        list_view = ListView(*players, id=PLAYER_LIST_ID)
        self.focus_element = list_view
        yield list_view
        yield Button("Start Game", id=START_GAME_BUTTON_ID, disabled=len(players) >= 2)

    def create_player_list(self):
        players = []
        for player in self.model.players:
            label = player
            if player == self.model.player_name:
                label += " (You)"
            players.append(ListItem(Label(label)))

        return players

    def update_list(self) -> None:
        player_list = self.query_one(f"#{PLAYER_LIST_ID}", ListView)
        players = self.create_player_list()
        player_list.clear()
        player_list.extend(players)

    @on(Button.Pressed)
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == START_GAME_BUTTON_ID:
            await self.controller.start_game()

    async def on_key(self, event) -> None:
        if event.key == "enter":
            await self.controller.start_game()

    def on_mount(self) -> None:
        self.focus_element.focus()
