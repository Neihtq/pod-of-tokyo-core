from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pod_of_tokyo_client.middleware.game_client import GameClient


@pytest.fixture
def game_client():
    with patch("socketio.AsyncClient") as mock_socketio_client:
        mock_sio_instance = MagicMock()
        mock_socketio_client.return_value = mock_sio_instance

        client = GameClient("http://localhost:10000")

        mock_sio_instance.connect = AsyncMock()
        mock_sio_instance.call = AsyncMock()
        mock_sio_instance.emit = AsyncMock()
        mock_sio_instance.wait = AsyncMock()
        mock_sio_instance.on = MagicMock()

        yield client


def test_constructor(game_client):
    assert game_client.sio is not None


@pytest.mark.asyncio
async def test_connect(game_client):
    game_client.set_get_name_handler(MagicMock())
    game_client.sio.call.return_value = {"playerName": "test_player"}
    await game_client.connect()
    game_client.sio.connect.assert_called_once_with("http://localhost:10000")
    game_client.sio.call.assert_called_once_with("get_name")
    game_client._get_name_handler.assert_called_once_with("test_player")


@pytest.mark.asyncio
async def test_event_handler(game_client):
    game_client.set_message_handler(AsyncMock())

    mock_sio_event = MagicMock()
    game_client.sio.event = mock_sio_event

    game_client._register_events()

    assert game_client.sio.event.call_count == 2
    assert game_client.sio.on.call_count == 1

    with patch("pod_of_tokyo_client.middleware.game_client.Message") as MockMessage:
        MockMessage.return_value = MagicMock()
        await game_client._message_handler("test_event", MockMessage.return_value)
        game_client._message_handler.assert_called_once_with(
            "test_event", MockMessage.return_value
        )
