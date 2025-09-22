import asyncio

from pod_of_tokyo_client.middleware.game_client import GameClient
from pod_of_tokyo_client.middleware.message import Message
from pod_of_tokyo_client.view.disabled_view import DisabledView
from pod_of_tokyo_client.view.lobby_view import LobbyView
from pod_of_tokyo_client.view.phase_1 import Phase1
from pod_of_tokyo_client.view.phase_2 import Phase2
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

    def get_name_handler(self, name):
        self.model.player_name = name
        self.view.compose_menu(LobbyView)

    async def connect(self, url):
        print("Creating game client!")
        url = "http://localhost:10000"
        self.client = GameClient(server_url=url)
        self.client.set_message_handler(self.handle_message)
        self.client.set_get_name_handler(self.get_name_handler)
        await self.client.connect()

    async def join_lobby(self, address: str):
        print("calling Controller.join_lobby")
        await self.connect(address)

    def update_lobby(self, players) -> None:
        print("Updating Lobby")
        self.model.players = players
        lobby_view = self.view.query_one(LobbyView)
        lobby_view.update_list()

    async def push_response_to_queue(self, response):
        await self.res_queue.put(response)

    async def handle_message(self, event_name, message: Message):
        print(f"Received message: event_name={event_name}, message={message}")
        message_type = MessageType(event_name)
        response = None
        if message_type == MessageType.LOBBY:
            self.update_lobby(message.members)
        elif (
            message_type == MessageType.START_GAME
            or message_type == MessageType.END_TURN
        ):
            self.view.compose_menu(DisabledView)
        elif message_type == MessageType.EVENT:
            self.update_events(message.message)
        elif message_type == MessageType.UPDATE:
            self.model.update_player_stats(message.player_update)
        elif message_type == MessageType.DEATH:
            self.model.alive = False
            self.view.compose_menu(DisabledView)
        else:
            response = await self.handle_interactive_message(message_type, message)

        return {"response": response}

    async def handle_interactive_message(self, message_type, message):
        if message_type == MessageType.ROLL:
            self.model.dices = []
            self.view.compose_menu(Phase1)
        elif message_type == MessageType.REROLL_AND_RESOLVE:
            self.model.dices = message.dices
            self.view.compose_menu(Phase2)
        elif message_type == MessageType.YIELD:
            self.view.compose_menu(YieldView)

        response = await self.res_queue.get()
        return response

    def handle_message_call(self, event_name, message):
        message_type = MessageType(event_name)
        if message_type == MessageType.UPDATE:
            self.model.update_player_stats(message.player_update)

    def update_events(self, event):
        print("Updating events")
        self.model.add_event(event)

    async def start_game(self):
        await self.client.send_message("start_game")

    async def confirm(self):
        await self.push_response_to_queue("ACK")

    async def throw_dices(self):
        print("sending response to throw dices")
        await self.push_response_to_queue("Throw")

    async def resolve_dices(self, dices):
        self.view.compose_menu(DisabledView)
        await self.push_response_to_queue({"dices": dices})

    async def yielding(self, is_yielding):
        self.view.compose_menu(DisabledView)
        await self.push_response_to_queue({"isYielding": is_yielding})
