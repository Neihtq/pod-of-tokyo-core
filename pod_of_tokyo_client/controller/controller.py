from pod_of_tokyo_client.view.lobby_view import LobbyView
from pod_of_tokyo_client.view.phase_1 import Phase1
from pod_of_tokyo_client.view.phase_2 import Phase2
from pod_of_tokyo_client.view.start_view import StartView
from pod_of_tokyo_client.view.view import PodOfTokyoView
from pod_of_tokyo_client.view.yield_view import YieldView


class Controller:
    def __init__(self, model):
        self.model = model

    def set_view(self, view: PodOfTokyoView):
        self.view = view

    def set_url(self, url):
        self.url = url

    def update_model(self):
        pass

    def get_view(self, view_class):
        return view_class(model=self.model, controller=self)

    def join_lobby(self, address: str):
        self.set_url(address)
        self.model.players = ["Godzilla", "Kinguin", "Alienoid (you)", "Woogie Boogie"]
        self.model.add_event("You joined the lobby")
        self.view.compose_menu(LobbyView)

    def start_game(self):
        self.model.dices = ["1", "2", "FIST", "FIST", "FIST", "FIST"]
        self.model.add_event("You started!")
        self.view.compose_menu(StartView)

    def init_phase_1(self):
        self.view.compose_menu(Phase1)

    def throw_dices(self):
        self.model.dices = ["1", "2", "THUNDER", "THUNDER", "HEART", "FIST"]
        self.model.add_event("You threw dices!")
        self.view.compose_menu(Phase2)

    def resolve_dices(self, dices):
        self.model.dices = ["1", "2", "THUNDER", "THUNDER", "HEART", "FIST"]
        self.model.add_event(f"Dices were chosen {dices}!")
        self.model.update_player_stats(health=1, score=5)
        self.view.compose_menu(YieldView)

    def is_yielding(self, will_yield):
        self.model.add_event(f"Did you yield?! {will_yield}")
        self.init_phase_1()
