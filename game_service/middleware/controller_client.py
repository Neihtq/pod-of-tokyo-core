import grpc
from google.protobuf.empty_pb2 import Empty
from pod_of_tokyo_commons.constants import OUTSIDE_KEY, TOKYO_BAY_KEY, TOKYO_CITY_KEY
from proto import controller_service_pb2 as pb2
from proto import controller_service_pb2_grpc as pb2_grpc

from entities.player import Player


class ControllerClient:
    def __init__(self, controller_url):
        self.controller_url = controller_url
        channel = grpc.insecure_channel(controller_url)
        self.stub = pb2_grpc.ControllerServiceStub(channel)

    def init_game(self, players: list[Player]) -> dict:
        request = pb2.InitGameRequest(
            players=[
                pb2.PlayerInput(player_id=p.player_id, pod_name=p.player_name)
                for p in players
            ]
        )
        response = self.stub.InitGame(request)
        return {
            "players": [
                {"playerId": p.player_id, "name": p.name, "podUrl": p.pod_url}
                for p in response.players
            ],
            "locations": list(response.locations),
        }

    def destroy_tokyo_bay(self):
        response = self.stub.DestroyTokyoBay(Empty())
        return {"playerId": response.player_id or None}

    def get_pod_url(self, player_id: str):
        request = pb2.GetPodUrlRequest(player_id=player_id)
        response = self.stub.GetPodUrl(request)
        return response.pod_url

    def destroy_all(self):
        self.stub.DestroyAll(Empty())

    def relocate(self, player_id: str, current_location: str, target_location: str):
        request = pb2.RelocateRequest(
            player_id=player_id,
            current_location=current_location,
            target_location=target_location,
        )
        self.stub.Relocate(request)

    def destroy_pod(self, player_id: str, location: str):
        request = pb2.DestroyPodRequest(player_id=player_id, location=location)
        self.stub.DestroyPod(request)

    def get_node_state(self):
        response = self.stub.GetNodeState(Empty())
        return {
            TOKYO_CITY_KEY: response.tokyo_city or None,
            TOKYO_BAY_KEY: response.tokyo_bay or None,
            OUTSIDE_KEY: list(response.outside),
        }

    def get_fleet_status(self):
        response = self.stub.GetFleetStatus(Empty())
        return list(response.fleet_status)
