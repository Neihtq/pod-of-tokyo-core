import asyncio

import socketio

from pod_of_tokyo_client.middleware.message import Message


class GameClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.sio = socketio.AsyncClient()
        self._register_events()

    def set_message_handler(self, handler):
        self._message_handler = handler

    def set_get_name_handler(self, handler):
        self._get_name_handler = handler

    def _register_events(self):
        @self.sio.event
        async def connect():
            print("Connection established")

        @self.sio.event
        async def disconnect():
            print("Disconnected from server")

        @self.sio.on("*")
        async def event_handler(event_name, data):
            return await self._message_handler(event_name, Message(data))

    async def connect(self):
        print(f"Connecting to server: {self.server_url}")
        await self.sio.connect(self.server_url)
        response = await self.sio.call("get_name")
        print(f"After connecting, received name {response}")
        self._get_name_handler(response["playerName"])
        asyncio.create_task(self.sio.wait())

    async def send_message(self, message):
        await self.sio.emit(message)
