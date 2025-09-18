from pod_of_tokyo_client.view.lobby_view import LobbyView
from pod_of_tokyo_client.view.phase_1 import Phase1
from pod_of_tokyo_client.view.phase_2 import Phase2
from pod_of_tokyo_client.view.start_view import StartView
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
        self.model.players = ["Godzilla", "Kinguin", "Alienoid (you)", "Woogie Boogie"]

        lobby_view = LobbyView(model=self.model, controller=self)
        self.view.compose_menu(lobby_view)

    def start_game(self):
        self.model.dices = ["1", "2", "FIST", "FIST", "FIST", "FIST"]
        start_view = StartView(model=self.model, controller=self)
        self.view.compose_menu(start_view)

    def init_phase_1(self):
        phase_1_view = Phase1(model=self.model, controller=self)
        self.view.compose_menu(phase_1_view)

    def throw_dices(self):
        self.model.dices = ["1", "2", "THUNDER", "THUNDER", "HEART"]
        phase_2_view = Phase2(model=self.model, controller=self)
        self.view.compose_menu(phase_2_view)
