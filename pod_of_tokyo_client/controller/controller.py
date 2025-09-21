import asyncio
import threading

from pod_of_tokyo_client.middleware.game_client import GameClient
from pod_of_tokyo_client.middleware.message import Message
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
        self.res_queue = asyncio.Queue()

    def get_view(self, view_class):
        return view_class(model=self.model, controller=self)

    def set_view(self, view: PodOfTokyoView):
        self.view = view

    def _connect(self, url):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.client = GameClient(server_url=url)
        self.client.set_message_handler(self.handle_message)
        asyncio.get_event_loop().run_until_complete(self.client.connect())
        asyncio.get_event_loop().close()

    def get_name_handler(self, name):
        self.model.player_name = name
        self.view.compose_menu(LobbyView)

    def connect(self, url):
        self.sio_thread = threading.Thread(
            target=self._connect, args=(url,), daemon=True
        )
        self.sio_thread.start()

    def join_lobby(self, address: str):
        self.connect(address)

    def update_lobby(self, players) -> None:
        self.model.players = players
        lobby_view = self.view.query_one(LobbyView)
        lobby_view.update_list()

    async def push_response_to_queue(self, response):
        asyncio.run_coroutine_threadsafe(
            self.res_queue.put(response), asyncio.get_event_loop()
        )

    def handle_message(self, event_name, message: Message):
        message_type = MessageType(event_name)
        response = None
        if message_type == MessageType.LOBBY:
            self.update_lobby(message.members)
        elif message_type == MessageType.EVENT:
            self.update_events(message.message)
        elif message_type == MessageType.UPDATE:
            self.model.update_player_stats(message.player_update)
        elif message_type == MessageType.DEATH:
            pass
        else:
            response = self.handle_interactive_message(message_type, message)

        return {"response": response}

    def handle_interactive_message(self, message_type, message):
        if message_type == MessageType.ROLL:
            self.model.dices = []
            self.view.compose_menu(Phase1)
        elif message_type == MessageType.REROLL_AND_RESOLVE:
            self.model.dices.extend(message.dices)
            self.view.compose_menu(Phase2)
        elif message_type == MessageType.YIELD:
            self.view.compose_menu(YieldView)

        return self.res_queue.get()

    def handle_message_call(self, event_name, message):
        message_type = MessageType(event_name)
        if message_type == MessageType.UPDATE:
            self.model.update_player_stats(message.player_update)

    def update_events(self, event):
        self.model.add_event(event)

    async def start_game(self):
        await self.client.send_message("start_game")
        self.view.compose_menu(StartView)

    async def confirm(self):
        await self.push_response_to_queue("ACK")

    async def throw_dices(self):
        await self.push_response_to_queue("Throw")
