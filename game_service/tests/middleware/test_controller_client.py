import unittest
from unittest.mock import patch

from google.protobuf.wrappers_pb2 import StringValue
from proto import controller_service_pb2 as pb2

from game_service.entities.player import Player
from game_service.middleware.controller_client import ControllerClient


class TestControllerClient(unittest.TestCase):

    @patch("grpc.insecure_channel")
    @patch("proto.controller_service_pb2_grpc.ControllerServiceStub")
    def setUp(self, mock_insecure_channel, mock_controller_service_stub):
        self.namespaces = ["city", "bay", "outside"]
        mock_insecure_channel.return_value = None
        self.mock_stub = mock_controller_service_stub.return_value
        with patch(
            "game_service.middleware.controller_client.pb2_grpc.ControllerServiceStub"
        ) as mock_stub:
            mock_stub.return_value = self.mock_stub
            self.base_url = "http://mock-controller-service"
            self.client = ControllerClient(self.base_url)

    def test_init_controller_client(self):
        self.assertEqual(self.client.controller_url, "http://mock-controller-service")

    def test_init_game(self):
        player_id = "playerId"
        player_name = "playerName"
        pod_url = "some.url"
        input_players = [Player(player_id, player_name)]

        processed_players = [
            pb2.Player(player_id=player_id, name=player_name, pod_url=pod_url)
        ]
        response = pb2.InitGameResponse(
            players=processed_players, locations=self.namespaces
        )
        self.mock_stub.InitGame.return_value = response

        result = self.client.init_game(input_players)

        expected = {
            "players": [
                {"playerId": p.player_id, "name": p.name, "podUrl": p.pod_url}
                for p in response.players
            ],
            "locations": list(response.locations),
        }
        self.assertEqual(result, expected)
        self.mock_stub.InitGame.assert_called_once()

    def test_destroy_tokyo_bay_returns_player(self):
        player_id = "playerId"
        response = pb2.DestroyTokyoBayResponse(player_id=StringValue(value=player_id))
        self.mock_stub.DestroyTokyoBay.return_value = response

        result = self.client.destroy_tokyo_bay()

        expected = {"playerId": player_id}
        self.assertEqual(result, expected)
        self.mock_stub.DestroyTokyoBay.assert_called_once()

    def test_destroy_tokyo_bay_returns_none(self):
        response = pb2.DestroyTokyoBayResponse(player_id=StringValue(value=None))
        self.mock_stub.DestroyTokyoBay.return_value = response

        result = self.client.destroy_tokyo_bay()

        expected = {"playerId": None}
        self.assertEqual(result, expected)
        self.mock_stub.DestroyTokyoBay.assert_called_once()

    def test_get_pod_url_returns_url(self):
        player_id = "playerId"
        pod_url = "some.url"
        response = pb2.GetPodUrlResponse(pod_url=pod_url)
        self.mock_stub.GetPodUrl.return_value = response

        result = self.client.get_pod_url(player_id)

        self.assertEqual(result, pod_url)
        self.mock_stub.GetPodUrl.assert_called_once()

    def test_destroy_all(self):
        response = pb2.DestroyAllResponse(status="success")
        self.mock_stub.DestroyAll.return_value = response

        self.client.destroy_all()

        self.mock_stub.DestroyAll.assert_called_once()

    def test_relocate(self):
        response = pb2.RelocateResponse(status="success")
        self.mock_stub.Relocate.return_value = response
        player_id = "player_id"
        curr_location = "city"
        target_location = "outside"

        self.client.relocate(
            player_id=player_id,
            current_location=curr_location,
            target_location=target_location,
        )

        self.mock_stub.Relocate.assert_called_once()

    def test_destroy_pod(self):
        player_id = "player_id"
        location = "outside"
        response = pb2.DestroyPodResponse(status="success")
        self.mock_stub.DestroyPod.return_value = response

        self.client.destroy_pod(player_id=player_id, location=location)

        self.mock_stub.DestroyPod.assert_called_once()

    def test_get_node_state(self):
        response = pb2.GetNodeStateResponse(
            tokyo_city="tokyo-city", tokyo_bay="tokyo-bay", outside="outside"
        )
        self.mock_stub.GetNodeState.return_value = response

        self.client.get_node_state()

        self.mock_stub.GetNodeState.assert_called_once()

    def test_get_fleet_status(self):
        fleet_status = "ACTIVE"
        response = pb2.GetFleetStatusResponse(fleet_status=[fleet_status])
        self.mock_stub.GetFleetStatus.return_value = response

        result = self.client.get_fleet_status()

        expected = [fleet_status]
        self.assertEqual(result, expected)
        self.mock_stub.GetFleetStatus.assert_called_once()

    def test_all_whenn_pb2_fails(self):
        for mock_call in [
            self.mock_stub.InitGame,
            self.mock_stub.DestroyTokyoBay,
            self.mock_stub.GetPodUrl,
            self.mock_stub.DestroyAll,
            self.mock_stub.Relocate,
            self.mock_stub.DestroyPod,
            self.mock_stub.GetNodeState,
            self.mock_stub.GetFleetStatus,
        ]:
            # TODO: Mock throwing error
            pass
