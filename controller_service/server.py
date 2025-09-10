from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/")
def ping():
    return "Alive"


@app.route("/initGame", methods=["POST"])
def init_game():
    data = request.get_json()
    player_ids = data.get("playerIds")
    return jsonify({"players": [{"playerId": "place_holder", "name": "place_holder"}]})


@app.route("/destroyTokyoBay", methods=["POST"])
def destroy_tokyo_bay():
    return jsonify({"playerId": "place_holder"})


@app.route("/getPodUrl", methods=["POST"])
def get_pod_url():
    data = request.get_json()
    player_id = data.get("playerId")
    return jsonify({"podUrl": "place_holder"})


@app.route("/destroyAll", methods=["POST"])
def destroy_all():
    return jsonify({"status": "success"})


@app.route("/relocate", methods=["POST"])
def relocate():
    data = request.get_json()
    player_id = data.get("playerId")
    location = data.get("location")
    return jsonify({"satus": "success"})


@app.route("/destroyPod", methods=["POST"])
def destroy_pod():
    data = request.get_json()
    player_id = data.get("playerId")
    return jsonify({"status": "success"})


@app.route("/getNodeStates", methods=["POST"])
def get_node_states():
    return jsonify({"tokyoCity": "place_holder", "tokyoBay": None, "outside": []})
