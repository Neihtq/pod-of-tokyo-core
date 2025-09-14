import random
import subprocess

from flask import Flask, jsonify, request
from kube.kube_dao import KubeDao

MONSTER_NAMES = [
    "alienoid",
    "boogie-woogie",
    "giga-zaur",
    "the-king",
    "kraken",
    "meka-dragon",
    "pandakai",
    "pumpkin-jack",
    "space-penguin",
]

TOKYO_CITY_KEY = "tokyo-city"
TOKYO_BAY_KEY = "tokyo-bay"
OUTSIDE_KEY = "outside"

LOCATION_NAMES = [
    TOKYO_CITY_KEY,
    TOKYO_BAY_KEY,
    OUTSIDE_KEY,
]


def join_url(ip, port):
    return f"{ip}:{port}"


class ControllerServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.kube_dao = KubeDao()
        self.ip = self.kube_dao.get_ip()

        self.players_by_id = {}
        self.player_ids_by_name = {}
        self.location_by_namespace = {}
        self.namespace_by_location = {}

        @self.app.route("/")
        def ping():
            return "Alive"

        @self.app.route("/initGame", methods=["POST"])
        def init_game():
            data = request.get_json()
            player_ids = data.get("playerIds")

            self.kube_dao.create_namespaces(LOCATION_NAMES)
            namespaces = self.kube_dao.list_all_namespaces()
            for ns in namespaces:
                self.location_by_namespace[ns["name"]] = ns["location"]
                self.namespace_by_location[ns["location"]] = ns["name"]

            monster_names = random.sample(MONSTER_NAMES, len(player_ids))
            players = []
            for i in range(len(player_ids)):
                player_id = player_ids[i]
                pod_name = monster_names[i]
                port = self.kube_dao.create_pod(
                    pod_name=pod_name,
                    namespace=self.namespace_by_location[OUTSIDE_KEY],
                )
                pod_url = join_url(self.ip, port)
                players.append(
                    {
                        "playerId": player_id,
                        "name": pod_name,
                        "podUrl": pod_url,
                    }
                )
                self.players_by_id[player_id] = (pod_name, pod_url)
                self.player_ids_by_name[pod_name] = player_id

                print(f"Successfully created pod '{pod_name}' listening on {pod_url}")

            return jsonify({"players": players, "locations": {}})

        @self.app.route("/destroyTokyoBay", methods=["POST"])
        def destroy_tokyo_bay():
            tokyo_bay_ns_name = self.namespace_by_location[TOKYO_BAY_KEY]

            pods_by_namespaces = self.kube_dao.list_all_pods()
            pod_in_bay = pods_by_namespaces[tokyo_bay_ns_name][0]

            outside_namespace = self.namespace_by_location[OUTSIDE_KEY]
            self.kube_dao.move_pod(
                pod_name=pod_in_bay,
                from_namespace=tokyo_bay_ns_name,
                target_namespace=outside_namespace,
            )

            self.kube_dao.delete_namespace(tokyo_bay_ns_name)

            return jsonify({"playerId": pod_in_bay})

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

            target_namespace = self.namespace_by_location[target_location]
            curr_namespace = self.namespace_by_location[curr_location]
            pod_name = self.players_by_id[player_id][0]
            print(
                f"Receive request to relocate '{pod_name}' ({player_id}) to '{target_location}' ({target_namespace})"
            )
            self.kube_dao.move_pod(
                pod_name,
                from_namespace=curr_namespace,
                target_namespace=target_namespace,
            )
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
                if self.location_by_namespace[namespace] == TOKYO_CITY_KEY:
                    response[TOKYO_CITY_KEY] = pods[0]
                elif self.location_by_namespace[namespace] == TOKYO_BAY_KEY:
                    response[TOKYO_BAY_KEY] = pods[0]
                else:
                    response[OUTSIDE_KEY] = pods
            return jsonify(response)
