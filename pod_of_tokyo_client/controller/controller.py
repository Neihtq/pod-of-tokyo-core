from textual.containers import Grid

from pod_of_tokyo_client.utils.constants import MENU_BOX_ID
from pod_of_tokyo_client.view.join_view import JoinView
from pod_of_tokyo_client.view.lobby_view import LobbyView
from pod_of_tokyo_client.view.view import PodOfTokyoView


class Controller:
    def __init__(self, model):
        self.model = model

    def set_view(self, view: PodOfTokyoView):
        self.view = view

    def handle_input(self, user_input):
        pass

    def update_model(self):
        pass

    def join_lobby(self, address: str):
        print(f"join lobby at address {address}")
        self.model.players = ["Godzilla", "Kinguin", "Alienoid (you)", "Woogie Boogie"]

        lobby_view = LobbyView(model=self.model, controller=self)
        self.view.compose_menu(lobby_view)

    def start_game(self):
        pass
