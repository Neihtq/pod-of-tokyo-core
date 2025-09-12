import random

from flask import Flask, jsonify, request
from kubernetes.kube_dao import KubeDao

MONSTER_NAMES = [
    "Alienoid",
    "Boogie Woogie",
    "Giga Zaur",
    "The King",
    "Kraken",
    "Meka Dragon",
    "Pandakai",
    "Pumpkin Jack",
    "Space Penguin",
]


def join_url(ip, port):
    return f"{ip}:{port}"


class ControllerServer:
    def __init__(self, host="0.0.0.0", port=8000):
        self.app = Flask(__name__)
        self.beginning_port = 8001
        self.kube_dao = KubeDao()

        self.players_by_id = {}
        self.player_ids_by_name = {}
        self.ip = None
        self.location_by_node_name = {}
        self.node_name_by_location = {}

        @self.app.route("/")
        def ping():
            return "Alive"

        @self.app.route("/initGame", methods=["POST"])
        def init_game():
            print("Received request for /initGame")
            self.kube_dao.spawn_nodes(["Tokyo City", "Tokyo Bay", "Outside"])
            self.ip = self.kube_dao.get_ip()
            print(f"Minikube started successfully. IP address: {self.ip}")

            nodes = self.kube_dao.list_all_nodes()
            for node in nodes:
                self.location_by_node_name[node["name"]] = node["location"]
                self.location_by_node_name[node["location"]] = node["name"]

            data = request.get_json()
            player_ids = data.get("playerIds")
            monster_names = random.sample(MONSTER_NAMES, len(player_ids))

            players = []
            for i in range(len(player_ids)):
                player_id = player_ids[i]
                name = monster_names[i]
                port = self.kube_dao.create_pod(
                    pod_name=name, node_name="Outside", node_port=self.beginning_port
                )
                pod_url = join_url(self.ip, port)
                players.append({"playerId": player_id, "name": name, "podUrl": pod_url})
                self.players_by_id[player_id] = (name, pod_url)
                self.player_ids_by_name[name] = player_id

                self.beginning_port += 1
                print(f"Successfully created pod '{name}' listening on {pod_url}")

            return jsonify({"players": players})

        @self.app.route("/destroyTokyoBay", methods=["POST"])
        def destroy_tokyo_bay():
            tokyo_bay_node_name = self.node_name_by_location["Tokyo Bay"]

            pods_by_nodes = self.kube_dao.list_all_pods()
            pod_in_bay = pods_by_nodes[tokyo_bay_node_name][0]

            outside_node_name = self.node_name_by_location["Outside"]
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
            location = data.get("location")

            pod_name = self.players_by_id[player_id][0]
            self.kube_dao.move_pod(pod_name, location)
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
                if self.location_by_node_name[node_name] == "Tokyo City":
                    response["tokyoCity"] = self.player_ids_by_name[pods][0]
                elif self.location_by_node_name[node_name] == "Tokyo Bay":
                    response["tokyoBay"] = self.player_ids_by_name[pods][0]
                else:
                    response["outside"] = self.player_ids_by_name[pods]

            return jsonify(response)

    def run(self, host="0.0.0.0", port=8000, debug=True):
        self.app.run(host=host, port=port, debug=debug)
