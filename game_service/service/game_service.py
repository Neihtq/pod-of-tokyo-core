import time
from collections import Counter, defaultdict

from flask_socketio import SocketIO
from pod_of_tokyo_commons.constants import OUTSIDE_KEY, TOKYO_BAY_KEY, TOKYO_CITY_KEY
from pod_of_tokyo_commons.entities import DiceSymbols, GameState, Player
from pod_of_tokyo_commons.model import Location, MessageType, PodStatus
from pod_of_tokyo_commons.model.update_event import UpdateEvent

from game_service.middleware.controller_client import ControllerClient
from game_service.middleware.pod_client import PodClient
from game_service.service.dice_service import roll_dices
from game_service.utils.constants import ROOM

WINNING_CONDITION = 20


class GameService:
    def __init__(self, socketio: SocketIO, controller_url):
        self.socketio = socketio
        self.players = {}
        self.player_order = []
        self.dead = set()
        self.controller = ControllerClient(base_url=controller_url)
        self.winner = None
        self.num_players_alive = 0
        self.turn = 0

    def get_game_state(self):
        game_state = defaultdict(list)
        for p_id in self.player_order:
            if p_id in self.dead:
                continue
            pod = self.players[p_id]
            health, score, energy, location = pod.get_state()
            game_state[location].append(
                Player(health=health, score=score, energy=energy, location=location)
            )
        return GameState(game_state)

    def remove(self, sid):
        if sid in self.players:
            del self.players[sid]

    def wait_for_game_ready(self):
        print("Waiting for fleet to be ready")
        ready = False
        while not ready:
            fleet_status = self.controller.get_fleet_status()
            ready = all(status == PodStatus.ACTIVE.value for status in fleet_status)
            time.sleep(5)

    def start_game(self):
        self.notify_all("Initializing game...")
        game_data = self.controller.init_game(
            [
                {player_id: player_name}
                for player_id, player_name in self.players.items()
            ]
        )
        players = game_data["players"]
        for p in players:
            player_id = p["playerId"]
            self.players[player_id] = PodClient(
                base_url=p["podUrl"], name=p["name"], player_id=p["playerId"]
            )
            self.player_order.append(player_id)
            update = UpdateEvent(location=Location.OUTSIDE, health=10)
            self.send_player_update(player_update=update, player_id=player_id)

        self.num_players_alive = len(self.player_order)

        key_to_location_map = {
            TOKYO_CITY_KEY: Location.CITY,
            TOKYO_BAY_KEY: Location.BAY,
            OUTSIDE_KEY: Location.OUTSIDE,
        }
        self.locations = {
            location: key_to_location_map[location]
            for location in game_data["locations"]
        }
        self.notify_all_game_start()
        self.wait_for_game_ready()
        self.notify_all("Game started!")

    def game_loop(self):
        self.start_game()
        idx = self.decide_starter()
        while not self.winner:
            player_id = self.player_order[idx]
            if player_id in self.dead:
                idx += 1
                continue

            name = self.players[player_id].name
            self.notify_all(f"It's {name}'s turn.")
            self.start_turn(player_id)
            idx = (idx + 1) % len(self.player_order)
            self.notify_turn_end((player_id))
            self.turn += 1

        self.notify_all(f"{self.winner.name} is King of Tokyo!")
        self.controller.destroy_all()
        self.__init__(self.socketio, self.controller.base_url)

    def start_turn(self, player_id):
        print(f"Beginning turn of {player_id}")
        pod = self.players[player_id]
        _, score, _, location_key = pod.get_state()

        location = self.locations[location_key]
        if not self.is_in_tokyo(location_key=location_key):
            score, location_key = self.fill_empty_space(pod, score)
            if location_key:
                location = self.locations[location_key]
        else:
            pod.update_score(2)
            score += 2
            player_update = UpdateEvent(location=location, score=2)
            self.send_player_update(player_update, pod.player_id)
            self.notify_all(f"{pod.name} received 2 stars!")

        if self.check_winner(pod, score):
            return

        dices = self.reroll_dices(pod)
        self.resolve_dices(pod, dices, location)

        if location == Location.OUTSIDE:
            score, _ = self.fill_empty_space(pod, score)

        self.check_winner(pod, score)

    def is_in_tokyo(self, location_key=None, location=None):
        tokyo_locations = {Location.CITY, Location.BAY}
        if location_key:
            return self.locations[location_key] in tokyo_locations

        return location in tokyo_locations

    def fill_empty_space(self, pod, score):
        node_state = self.controller.get_node_state()
        location_key = None
        if node_state[TOKYO_CITY_KEY] is None:
            location_key = TOKYO_CITY_KEY
        elif self.num_players_alive > 4 and node_state[TOKYO_BAY_KEY] is None:
            location_key = TOKYO_BAY_KEY

        if location_key:
            location = self.locations[location_key]
            self.notify_all(f"{pod.name} enters {location.value}!")
            self.controller.relocate(pod.player_id, OUTSIDE_KEY, location_key)
            pod.update_score(1)
            score += 1
            player_update = UpdateEvent(location=location, score=1)
            self.send_player_update(player_update, pod.player_id)
            self.notify_all(f"{pod.name} received 1 star!")

        return score, location_key

    def check_winner(self, pod, score):
        is_winner = score == WINNING_CONDITION or (
            len(self.player_order) - len(self.dead) == 1
            and pod.player_id not in self.dead
        )
        if is_winner:
            self.winner = pod.name
            self.notify_all(f"{pod.name} is the King of Tokyo!")

        return is_winner

    def reroll_dices(self, pod: PodClient):
        self.call_and_wait(MessageType.ROLL, pod.player_id)
        num_dices = num_throws = 6
        throw_count = 0
        max_num_throws = 3
        dices_to_keep = []
        while throw_count < max_num_throws and num_throws > 0:
            dices = roll_dices(num_throws)
            self.notify_all(f"{pod.name} threw the dices! {dices}")

            response = self.call_and_wait(
                MessageType.REROLL_AND_RESOLVE, pod.player_id, {"dices": dices}
            )
            chosen_dices = response["dices"]
            dices_to_keep.extend(chosen_dices)
            self.notify_all(f"{pod.name} kept {dices_to_keep}")
            num_throws = num_throws - len(chosen_dices)
            throw_count += 1

        if len(dices_to_keep) < num_dices:
            remaining_dices = list((Counter(chosen_dices) - Counter(dices)).elements())
            dices_to_keep.extend(remaining_dices)

        return dices_to_keep

    def resolve_dices(self, pod, dices, location):
        self.notify_all(f"{pod.name} is resolving their dices: {dices}")
        counter = Counter(dices)
        for key in counter:
            amount = counter[key]
            if key == DiceSymbols.HEART.value:
                self.heal_player(pod, amount, location)
            elif key == DiceSymbols.FIST.value:
                self.slap(pod, location, damage=amount)
            elif key == DiceSymbols.THUNDER.value:
                pod.charge_energy(energy=amount)
                player_update = UpdateEvent(location=location, energy=amount)
                self.send_player_update(player_update, pod.player_id)
                self.notify_all(f"{pod.name} charged {amount} energy.")
            elif amount >= 3:
                score = int(key) + max(0, amount - 3) * int(key)
                pod.update_score(score=score)
                player_update = UpdateEvent(location=location, score=score)
                self.send_player_update(player_update, pod.player_id)
                msg_suffix = "star" if score == 1 else "stars"
                message = f"{pod.name} received {score} {msg_suffix}!"
                self.notify_all(message)

    def heal_player(self, pod, amount, location):
        if self.is_in_tokyo(location=location):
            self.notify_all(
                f"{pod.player_name} is in Tokyo! Healing in Tokyo is not possible!"
            )
            return
        health, _, _, _ = pod.get_state()
        if health < 10:
            amount = min(amount, 10 - health)
            pod.heal(health=amount)
            player_update = UpdateEvent(location=location, health=amount)
            self.send_player_update(player_update, pod.player_id)
            self.notify_all(f"{pod.name} healed {amount} life points.")

    def slap(self, active_pod, location, damage):
        if self.turn == 0:
            self.notify_all(
                f"The beginning player cannot slap other players on their first turn!"
            )
            return

        for p_id in self.player_order:
            if p_id in self.dead or p_id == active_pod.player_id:
                continue

            pod = self.players[p_id]
            health, _, _, p_location = pod.get_state()
            if self.locations[p_location] == location or (
                self.is_in_tokyo(location=location)
                and self.is_in_tokyo(location_key=p_location)
            ):
                continue

            pod.slap(damage)
            player_update = UpdateEvent(
                location=self.locations[p_location], damage=damage
            )
            self.send_player_update(player_update, p_id)
            self.notify_all(
                f"{active_pod.name} slapped {pod.name}! {pod.name} lost {damage} life points."
            )
            health -= damage
            if health <= 0:
                self.dead.add(p_id)
                self.num_players_alive -= 1
                self.controller.destroy_pod(p_id, p_location)
                self.notify_player_death(p_id)
                self.notify_all(f"{pod.name} died!")

                if self.num_players_alive <= 4:
                    self.destroy_tokyo_bay()

            elif self.is_in_tokyo(location_key=p_location):
                response = self.call_and_wait(MessageType.YIELD, p_id)
                if response["isYielding"]:
                    self.controller.relocate(p_id, p_location, OUTSIDE_KEY)
                    self.notify_all(f"{pod.name} is leaving Tokyo!")
                    player_update = UpdateEvent(location=Location.OUTSIDE)
                    self.send_player_update(player_update, p_id)

            time.sleep(0.5)

    def destroy_tokyo_bay(self):
        player_at_bay = self.controller.destroy_tokyo_bay()["playerId"]
        self.notify_all(f"Tokyo Bay has been flooded!")
        if player_at_bay:
            pod_at_bay = self.players[player_at_bay]
            self.notify_all(f"{pod_at_bay.name} is leaving Tokyo!")
            player_update = UpdateEvent(location=Location.OUTSIDE)
            self.send_player_update(player_update, player_at_bay)

    def call_and_wait(self, command: MessageType, player_id: str, payload={}):
        return self.socketio.call(command.value, payload, to=player_id, timeout=600)[
            "response"
        ]

    def send_player_update(self, player_update, player_id):
        payload = {"update": player_update.to_dict()}
        self.socketio.emit(MessageType.UPDATE.value, payload, to=player_id)

    def notify_player_death(self, player_id):
        self.socketio.emit(MessageType.DEATH.value, {}, to=player_id)

    def notify_all(self, message):
        game_state = self.get_game_state().to_dict()
        payload = {"message": message, "gameState": game_state}
        self.socketio.emit(MessageType.EVENT.value, payload, to=ROOM)
        time.sleep(0.5)

    def notify_all_game_start(self):
        self.socketio.emit(MessageType.START_GAME.value, {}, to=ROOM)

    def notify_turn_end(self, player_id):
        self.socketio.emit(MessageType.END_TURN.value, {}, to=player_id)

    def decide_starter(self):
        players = self.player_order.copy()
        winners = []
        max_score = 0
        self.notify_all("Determining who starts...")
        while len(winners) != 1:
            winners = []
            max_score = 0
            for player_id in players:
                dices = roll_dices(6)
                num_fists = Counter(dices)[DiceSymbols.FIST.value]
                if num_fists > max_score:
                    max_score = num_fists
                    winners = [player_id]
                elif num_fists == max_score:
                    winners.append(player_id)

            players = winners.copy()

        starter = winners[0]
        return self.player_order.index(starter)
