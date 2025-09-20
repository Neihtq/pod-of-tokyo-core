from pod_of_tokyo_client.middleware.game_client import GameClient
from pod_of_tokyo_client.view.lobby_view import LobbyView
from pod_of_tokyo_client.view.phase_1 import Phase1
from pod_of_tokyo_client.view.phase_2 import Phase2
from pod_of_tokyo_client.view.start_view import StartView
from pod_of_tokyo_client.view.view import PodOfTokyoView
from pod_of_tokyo_client.view.yield_view import YieldView
from pod_of_tokyo_commons.model import MessageType


class Controller:
    def __init__(self, model):
        self.model = model

    def get_view(self, view_class):
        return view_class(model=self.model, controller=self)

    def set_view(self, view: PodOfTokyoView):
        self.view = view

    def connect(self, url):
        self.client = GameClient(url)
        self.client.set_message_handler(self.handle_message)

    def handle_message(self, event_name, message):
        message_type = MessageType(event_name)
        if message_type == MessageType.EVENT:
            self.update_events(message.message)
        elif message_type == MessageType.ROLL:
            self.model.dices = []
            self.view.compose_menu(Phase1)
        elif message_type == MessageType.REROLL_AND_RESOLVE:
            self.model.dices.extend(message.dices)
            self.view.compose_menu(Phase2)
        elif message_type == MessageType.YIELD:
            self.view.compose_menu(YieldView)
        elif message_type == MessageType.UPDATE:
            self.model.update_player_stats(message.player_update)

    def update_events(self, event):
        self.model.add_event(event)

    def join_lobby(self, address: str):
        self.connect(address)
        self.view.compose_menu(LobbyView)

    def start_game(self):
        self.view.compose_menu(StartView)

    def confirm(self):
        pass

    def throw_dices(self):
        pass
