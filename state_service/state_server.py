import os

from flask import Flask, jsonify, request
from monster_db.monster_db_dao import MonsterDbDao


class StateServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.monster_db_dao = MonsterDbDao()
        self.healthy = os.environ["HEALTHY"] == "true"

        @self.app.route("/")
        def ping():
            return "Alive"

        @self.app.route("/healthz")
        def healthz():
            if self.healthy:
                return "OK", 200
            else:
                return "FAIL", 500

        @self.app.route("/slap", methods=["POST"])
        def slap():
            data = request.get_json()
            damage = data.get("damage")
            updated_health = self.monster_db_dao.decrease_health(amount=damage)

            return jsonify({"health": updated_health})

        @self.app.route("/heal", methods=["POST"])
        def heal():
            data = request.get_json()
            health = data.get("health")
            updated_health = self.monster_db_dao.increase_health(amount=health)

            return jsonify({"health": updated_health})

        @self.app.route("/updateScore", methods=["POST"])
        def update_score():
            data = request.get_json()
            points = data.get("points")
            updated_score = self.monster_db_dao.increase_score(amount=points)

            return jsonify({"score": updated_score})

        @self.app.route("/chargeEnergy", methods=["POST"])
        def charge_energy():
            data = request.get_json()
            energy = data.get("energy")
            updated_energy = self.monster_db_dao.increase_energy(amount=energy)

            return jsonify({"energy": updated_energy})

        @self.app.route("/updateLocation", methods=["POST"])
        def update_location():
            data = request.get_json()
            location = data.get("location")
            updated_location = self.monster_db_dao.update_location(location=location)

            return jsonify({"location": updated_location})

        @self.app.route("/getStats", methods=["POST"])
        def get_stats():
            return jsonify(self.monster_db_dao.get_stats())
