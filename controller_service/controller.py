from collections import defaultdict
from concurrent import futures

import grpc
from google.protobuf.empty_pb2 import Empty
from google.protobuf.wrappers_pb2 import StringValue

from controller_service.kube.kube_dao import KubeDao
from controller_service.middleware import pod_client
from pod_of_tokyo_commons.constants import (
    LOCATION_NAMES,
    OUTSIDE_KEY,
    TOKYO_BAY_KEY,
    TOKYO_CITY_KEY,
)
from pod_of_tokyo_commons.model import PodStatus
from proto import controller_service_pb2 as pb2
from proto import controller_service_pb2_grpc as pb2_grpc


def join_url(ip, port):
    return f"{ip}:{port}"


IP_ADDRESS = "http://127.0.0.1"


class ControllerService(pb2_grpc.ControllerServiceServicer):
    def __init__(self):
        self.kube_dao = KubeDao()
        self.ip = IP_ADDRESS
        self.state_service_port = 33333

        self.players_by_id = {}  # player_id -> (pod_name, pod_url, port)
        self.player_ids_by_name = {}  # pod_name -> player_id

    def GetFleetStatus(self, request: Empty, context):
        player_pods = self.kube_dao.list_all_pods()
        postgres_pods = self.kube_dao.get_postgres_pods()
        pod_by_namespace = defaultdict(list, {**player_pods, **postgres_pods})

        fleet_status = []
        for namespace, pods in pod_by_namespace.items():
            for pod_name in pods:
                if self.kube_dao.is_pod_active(pod_name=pod_name, namespace=namespace):
                    fleet_status.append(PodStatus.ACTIVE.value)
                else:
                    fleet_status.append(PodStatus.INACTIVE.value)

        return pb2.GetFleetStatusResponse(fleet_status=fleet_status)

    def InitGame(self, request, context):
        self.kube_dao.create_namespaces(LOCATION_NAMES)
        namespaces = self.kube_dao.list_all_namespaces()

        processed_players = []
        for player_input in request.players:
            player_id = player_input.player_id
            pod_name = player_input.pod_name

            self.kube_dao.create_pod(
                pod_name=pod_name,
                namespace=OUTSIDE_KEY,
                player_id=player_id,
                service_port=self.state_service_port,
            )
            pod_url = join_url(self.ip, self.state_service_port)
            processed_players.append(
                pb2.Player(player_id=player_id, name=pod_name, pod_url=pod_url)
            )
            self.players_by_id[player_id] = (
                pod_name,
                pod_url,
                self.state_service_port,
            )
            self.player_ids_by_name[pod_name] = player_id
            self.state_service_port += 1

            print(f"Successfully created pod '{pod_name}' listening on {pod_url}")

        return pb2.InitGameResponse(players=processed_players, locations=namespaces)

    def DestroyTokyoBay(self, request: Empty, context):
        pods_by_namespaces = self.kube_dao.list_all_pods()
        pods_in_bay = pods_by_namespaces[TOKYO_BAY_KEY]
        if not pods_in_bay:
            return pb2.DestroyTokyoBayResponse()

        pod_in_bay = pods_in_bay[0]
        player_id = self.player_ids_by_name[pod_in_bay]

        self.kube_dao.move_pod(
            pod_name=pod_in_bay,
            from_namespace=TOKYO_BAY_KEY,
            target_namespace=OUTSIDE_KEY,
            service_port=self.players_by_id[player_id][-1],
        )

        url = self.players_by_id[player_id][1]
        pod_client.update_monster_location(url=url, location=OUTSIDE_KEY)

        self.kube_dao.delete_namespace(TOKYO_BAY_KEY)

        return pb2.DestroyTokyoBayResponse(player_id=StringValue(value=player_id))

    def GetPodUrl(self, request, context):
        player_id = request.player_id
        pod_url = self.players_by_id[player_id][1]
        return pb2.GetPodUrlResponse(pod_url=pod_url)

    def DestroyAll(self, request: Empty, context):
        self.kube_dao.delete_all_namespaces()
        return pb2.DestroyAllResponse(status="success")

    def Relocate(self, request, context):
        player_id = request.player_id
        target_location = request.target_location
        curr_location = request.current_location

        pod_name = self.players_by_id[player_id][0]
        self.kube_dao.move_pod(
            pod_name,
            from_namespace=curr_location,
            target_namespace=target_location,
            service_port=self.players_by_id[player_id][-1],
        )

        url = self.players_by_id[player_id][1]
        pod_client.update_monster_location(url=url, location=target_location)

        return pb2.RelocateResponse(status="success")

    def DestroyPod(self, request, context):
        player_id = request.player_id
        player_location = request.location

        pod_name = self.players_by_id[player_id][0]
        self.kube_dao.kill_pod(
            player_id=player_id,
            pod_name=pod_name,
            namespace=player_location,
            service_port=self.players_by_id[player_id][-1],
        )

        return pb2.DestroyPodResponse(status="success")

    def GetNodeState(self, request: Empty, context):
        pods_by_namespace = self.kube_dao.list_all_pods()
        pod_locations = {TOKYO_CITY_KEY: "", TOKYO_BAY_KEY: "", OUTSIDE_KEY: []}

        for namespace, pods in pods_by_namespace.items():
            if namespace == TOKYO_CITY_KEY:
                pod_locations[TOKYO_CITY_KEY] = pods[0]
            elif namespace == TOKYO_BAY_KEY:
                pod_locations[TOKYO_BAY_KEY] = pods[0]
            else:
                pod_locations[OUTSIDE_KEY] = pods
        return pb2.GetNodeStateResponse(
            tokyo_city=pod_locations[TOKYO_CITY_KEY],
            tokyo_bay=pod_locations[TOKYO_BAY_KEY],
            outside=pod_locations[OUTSIDE_KEY],
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_ControllerServiceServicer_to_server(ControllerService(), server)
    server.add_insecure_port("[::]:11000")
    server.start()
    print("ControllerService gRPC server running on port 11000...")
    server.wait_for_termination()
