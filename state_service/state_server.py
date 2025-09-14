from flask import Flask, jsonify, request
from monster_db.monster_db_dao import MonsterDbDao


class StateServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.monster_db_dao = MonsterDbDao()
        self.monster_db_dao.create_monster()

        @self.app.route("/")
        def ping():
            return "Alive"

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
            updated_health = self.monster_db_dao.increase_energy(amount=health)

            return jsonify({"health": updated_health})

        @self.app.route("/updateScore", methods=["POST"])
        def update_score():
            data = request.get_json()
            points = data.get("points")
            updated_score = self.monster_db_dao.increase_score(amount=points)

            return jsonify({"score": updated_score})

        @self.app.route("/updateLocation", methods=["POST"])
        def update_location():
            data = request.get_json()
            location = data.get("location")
            updated_location = self.monster_db_dao.update_location(location=location)

            return jsonify({"location": updated_location})

        @self.app.route("/getState", methods=["POST"])
        def get_state(self):
            return jsonify(self.monster_db_dao.get_state())
