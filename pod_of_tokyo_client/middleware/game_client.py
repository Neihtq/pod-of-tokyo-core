import socketio

from pod_of_tokyo_client.middleware.message import Message


class GameClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.sio = socketio.Client()
        self._register_events()

    def set_message_handler(self, handler):
        self._message_handler = handler

    def _register_events(self):
        @self.sio.event
        async def connect():
            print("Connection established")

        @self.sio.event
        async def disconnect():
            print("Disconnected from server")

        @self.sio.event("*")
        async def event_handler(event_name, data):
            return self._message_handler(event_name, Message(data))

    async def connect(self):
        await self.sio.connect(self.server_url)
        await self.sio.wait()
