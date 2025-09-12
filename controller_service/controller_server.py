import random

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
        self.players_by_id = {}
        self.player_ids_by_name = {}
        self.ip = None
        self.location_by_node_name = {}
        self.node_name_by_location = {}

        self.app = Flask(__name__)
        self.kube_dao = KubeDao()
        self.setup_nodes()

        @self.app.route("/")
        def ping():
            return "Alive"

        @self.app.route("/initGame", methods=["POST"])
        def init_game():
            data = request.get_json()
            player_ids = data.get("playerIds")
            monster_names = random.sample(MONSTER_NAMES, len(player_ids))

            players = []
            for i in range(len(player_ids)):
                player_id = player_ids[i]
                pod_name = monster_names[i]
                port = self.kube_dao.create_pod(
                    pod_name=pod_name,
                    node_name=self.node_name_by_location[OUTSIDE_KEY],
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
            tokyo_bay_node_name = self.node_name_by_location[TOKYO_BAY_KEY]

            pods_by_nodes = self.kube_dao.list_all_pods()
            pod_in_bay = pods_by_nodes[tokyo_bay_node_name][0]

            outside_node_name = self.node_name_by_location[OUTSIDE_KEY]
            self.kube_dao.move_pod(pod_name=pod_in_bay, target_node=outside_node_name)

            self.kube_dao.delete_node(tokyo_bay_node_name)

            return jsonify({"playerId": pod_in_bay})

        @self.app.route("/getPodUrl", methods=["POST"])
        def get_pod_url():
            data = request.get_json()
            player_id = data.get("playerId")

            return jsonify({"podUrl": self.players_by_id[player_id][1]})

        @self.app.route("/destroyAll", methods=["POST"])
        def destroy_all():
            self.kube_dao.delete_all_nodes()
            return jsonify({"status": "success"})

        @self.app.route("/relocate", methods=["POST"])
        def relocate():
            data = request.get_json()
            player_id = data.get("playerId")
            target_location = data.get("targetLocation")

            target_node = self.node_name_by_location[target_location]
            pod_name = self.players_by_id[player_id][0]
            print(
                f"Receive request to relocate '{pod_name}' ({player_id}) to '{target_location}' ({target_node})"
            )
            self.kube_dao.move_pod(pod_name, target_node)
            return jsonify({"status": "success"})

        @self.app.route("/destroyPod", methods=["POST"])
        def destroy_pod():
            data = request.get_json()
            player_id = data.get("playerId")

            pod_name = self.players_by_id[player_id][0]
            self.kube_dao.delete_pod(pod_name)
            return jsonify({"status": "success"})

        @self.app.route("/getNodeStates", methods=["POST"])
        def get_node_states():
            pods_by_nodes = self.kube_dao.list_all_pods()
            response = {}

            for node_name, pods in pods_by_nodes.items():
                if self.location_by_node_name[node_name] == TOKYO_CITY_KEY:
                    response[TOKYO_CITY_KEY] = pods[0]
                elif self.location_by_node_name[node_name] == TOKYO_BAY_KEY:
                    response[TOKYO_BAY_KEY] = pods[0]
                else:
                    response[OUTSIDE_KEY] = pods
            return jsonify(response)

    def setup_nodes(self):
        print(f"Initialize minikube with nodes: {LOCATION_NAMES}")
        self.kube_dao.spawn_nodes(LOCATION_NAMES)
        self.ip = self.kube_dao.get_ip()
        print(f"Minikube started successfully. IP address: {self.ip}")

        nodes = self.kube_dao.list_all_nodes()
        for node in nodes:
            self.location_by_node_name[node["name"]] = node["location"]
            self.node_name_by_location[node["location"]] = node["name"]
        print(f"Node initialization succeeded")

    def run(self, host="0.0.0.0", port=11000, debug=True):
        self.app.run(host=host, port=port, debug=debug)
