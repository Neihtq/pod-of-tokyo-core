from flask import Flask, jsonify, request

from controller_service.kube.kube_dao import KubeDao
from controller_service.middleware import pod_client
from pod_of_tokyo_commons.constants import (
    LOCATION_NAMES,
    OUTSIDE_KEY,
    TOKYO_BAY_KEY,
    TOKYO_CITY_KEY,
)


def join_url(ip, port):
    return f"{ip}:{port}"


class ControllerServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.kube_dao = KubeDao()
        self.ip = "http://127.0.0.1"
        self.state_service_port = 33333

        self.players_by_id = {}
        self.player_ids_by_name = {}

        @self.app.route("/")
        def ping():
            return "Alive"

        @self.app.route("/initGame", methods=["POST"])
        def init_game():
            data = request.get_json()
            players = data.get("players")

            self.kube_dao.create_namespaces(LOCATION_NAMES)
            namespaces = self.kube_dao.list_all_namespaces()

            # Re-initialize players to an empty list to store processed player data
            processed_players = []
            for i in range(len(players)):
                for k in players[i]:
                    player_id = k
                    pod_name = players[i][k]

                port = self.kube_dao.create_pod(
                    pod_name=pod_name,
                    namespace=OUTSIDE_KEY,
                    player_id=player_id,
                    service_port=self.state_service_port,
                )
                pod_url = join_url(self.ip, self.state_service_port)
                processed_players.append(
                    {
                        "playerId": player_id,
                        "name": pod_name,
                        "podUrl": pod_url,
                    }
                )
                self.players_by_id[player_id] = (
                    pod_name,
                    pod_url,
                    self.state_service_port,
                )
                self.player_ids_by_name[pod_name] = player_id
                self.state_service_port += 1

                print(f"Successfully created pod '{pod_name}' listening on {pod_url}")

            print(self.players_by_id)
            print(self.player_ids_by_name)

            return jsonify({"players": processed_players, "locations": namespaces})

        @self.app.route("/destroyTokyoBay", methods=["POST"])
        def destroy_tokyo_bay():
            pods_by_namespaces = self.kube_dao.list_all_pods()
            pod_in_bay = pods_by_namespaces[TOKYO_BAY_KEY][0]
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

            return jsonify({"playerId": player_id})

        @self.app.route("/getPodUrl", methods=["POST"])
        def get_pod_url():
            data = request.get_json()
            player_id = data.get("playerId")

            return jsonify({"podUrl": self.players_by_id[player_id][1]})

        @self.app.route("/destroyAll", methods=["POST"])
        def destroy_all():
            self.kube_dao.delete_all_namespaces()
            return jsonify({"status": "success"})

        @self.app.route("/relocate", methods=["POST"])
        def relocate():
            data = request.get_json()
            player_id = data.get("playerId")
            target_location = data.get("targetLocation")
            curr_location = data.get("currentLocation")

            pod_name = self.players_by_id[player_id][0]
            print(
                f"Receive request to relocate '{pod_name}' ({player_id}) to '{target_location}' ({target_location})"
            )
            self.kube_dao.move_pod(
                pod_name,
                from_namespace=curr_location,
                target_namespace=target_location,
                service_port=self.players_by_id[player_id][-1],
            )

            url = self.players_by_id[player_id][1]
            pod_client.update_monster_location(url=url, location=target_location)

            return jsonify({"status": "success"})

        @self.app.route("/destroyPod", methods=["POST"])
        def destroy_pod():
            data = request.get_json()
            player_id = data.get("playerId")
            player_location = data.get("location")

            pod_name = self.players_by_id[player_id][0]
            self.kube_dao.delete_pod(pod_name, player_location)
            return jsonify({"status": "success"})

        @self.app.route("/getNodeState", methods=["POST"])
        def get_node_state():
            pods_by_namespace = self.kube_dao.list_all_pods()
            response = {}

            for namespace, pods in pods_by_namespace.items():
                if namespace == TOKYO_CITY_KEY:
                    response[TOKYO_CITY_KEY] = pods[0]
                elif namespace == TOKYO_BAY_KEY:
                    response[TOKYO_BAY_KEY] = pods[0]
                else:
                    response[OUTSIDE_KEY] = pods
            return jsonify(response)
