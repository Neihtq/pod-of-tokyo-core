import time
from collections import Counter, defaultdict

from flask_socketio import SocketIO, join_room
from pod_of_tokyo_commons.constants import OUTSIDE_KEY, TOKYO_BAY_KEY, TOKYO_CITY_KEY
from pod_of_tokyo_commons.entities import DiceSymbols, GameState, Player
from pod_of_tokyo_commons.model import MessageType
from pod_of_tokyo_commons.model.update_event import UpdateEvent

from game_service.middleware.controller_client import ControllerClient
from game_service.middleware.pod_client import PodClient
from game_service.model import Location
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

    def start_game(self):
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
            update = UpdateEvent(location=Location.OUTSIDE.value)
            self.send_player_update(player_update=update, player_id=player_id)

        self.num_players_alive = len(self.player_order)
        self.locations = {
            game_data["locations"][TOKYO_CITY_KEY]: Location.CITY,
            game_data["locations"][TOKYO_BAY_KEY]: Location.BAY,
            game_data["locations"][OUTSIDE_KEY]: Location.OUTSIDE,
        }
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

        self.notify_all(f"{self.winner.name} is King of Tokyo!")
        self.controller.destroy_all()
        self.__init__(self.socketio, self.controller.base_url)

    def start_turn(self, player_id):
        pod = self.players[player_id]
        _, score, _, location = pod.get_state()

        if not self.is_in_tokyo(location):
            score = self.fill_empty_space(pod, score)
        elif self.is_in_tokyo(location):
            pod.update_score(2)
            score += 2
            player_update = UpdateEvent(location=location, score=2)
            self.send_player_update(player_update, pod.player_id)
            self.notify_all(f"{pod.name} received 2 stars!")

        if self.check_winner(pod, score):
            return

        dices = self.reroll_dices(pod)
        self.resolve_dices(pod, dices, location)

        if self.locations[location] == Location.OUTSIDE:
            score = self.fill_empty_space(pod, score)

        self.check_winner(pod, score)

    def is_in_tokyo(self, location):
        return (
            self.locations[location] == Location.CITY
            or self.locations[location] == Location.BAY
        )

    def fill_empty_space(self, pod, score):
        node_state = self.controller.get_node_state()
        new_location = None
        if node_state[TOKYO_CITY_KEY] is None:
            new_location = Location.CITY
        elif self.num_players_alive > 4 and node_state[TOKYO_BAY_KEY] is None:
            new_location = Location.BAY

        if new_location:
            location_msg = (
                "Tokyo City" if new_location == Location.CITY else "Tokyo Bay"
            )
            self.controller.relocate(
                pod.player_id, Location.OUTSIDE.value, new_location.value
            )
            self.notify_all(f"{pod.name} has conquered {location_msg}!")
            pod.update_score(1)
            score += 1
            player_update = UpdateEvent(location=new_location.value, score=1)
            self.send_player_update(player_update, pod.player_id)
            self.notify_all(f"{pod.name} received 1 star!")

        return score

    def check_winner(self, pod, score):
        is_winner = score == WINNING_CONDITION or (
            len(self.player_order) - len(self.dead) == 1
            and pod.player_id not in self.dead
        )
        if is_winner:
            self.winner = pod.name
            self.notify_all(f"{pod.name} is the King of Tokyo!")

        return is_winner

    def reroll_dices(self, pod):
        num_throws = 6
        throw_count = 0
        dices_to_keep = []
        max_num_throws = 3
        while throw_count < max_num_throws and num_throws > 0:
            dices = roll_dices(num_throws)
            self.notify_all(f"{pod.name} threw the dices! {dices}")

            response = self.call_and_wait(
                MessageType.REROLL_AND_RESOLVE, pod.player_id, {"dices": dices}
            )
            chosen_dices = response["dicesToKeep"]
            dices_to_keep.extend(chosen_dices)
            self.notify_all(f"{pod.name} kept {dices_to_keep}")
            num_throws = num_throws - len(chosen_dices)
            throw_count += 1

        return dices_to_keep

    def resolve_dices(self, pod, dices, location):
        counter = Counter(dices)
        for key in counter:
            amount = counter[key]
            if key == DiceSymbols.HEART.value:
                pod.heal(life=amount)
                player_update = UpdateEvent(location=location, health=amount)
                self.send_player_update(player_update, pod.player_id)
                self.notify_all(f"{pod.name} healed {amount} life points.")
            if key == DiceSymbols.FIST.value:
                self.slap(pod, location, damage=amount)

            if key == DiceSymbols.THUNDER.value:
                pod.charge_energy(energy=amount)
                player_update = UpdateEvent(location=location, energy=amount)
                self.send_player_update(player_update, pod.player_id)
                self.notify_all(f"{pod.name} charged {amount} energy.")

        num_counter = 0
        score = 0
        score_threshold = 3
        for num in [DiceSymbols.ONE, DiceSymbols.TWO, DiceSymbols.THREE]:
            if num.value in counter:
                num_counter += counter[num.value]
                score += int(num.value) * counter[num.value]  # type:ignore
        if num_counter >= score_threshold:
            pod.update_score(score=score)
            player_update = UpdateEvent(location=location, score=score)
            self.send_player_update(player_update, pod.player_id)
            msg_suffix = "star" if score == 1 else "stars"
            message = f"{pod.name} received {score} {msg_suffix}!"
            self.notify_all(message)

    def slap(self, active_pod, location, damage):
        for p_id in self.player_order:
            if p_id in self.dead or p_id == active_pod.player_id:
                continue

            pod = self.players[p_id]
            health, _, _, p_location = pod.get_state()
            if p_location == location:
                continue

            pod.slap(damage)
            player_update = UpdateEvent(location=p_location, damage=damage)
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
                    player_at_bay = self.controller.destroy_tokyo_bay()["playerId"]
                    self.notify_all(f"Tokyo Bay has been flooded!")
                    if player_at_bay:
                        pod_at_bay = self.players[player_at_bay]
                        player_update = UpdateEvent(location=Location.OUTSIDE.value)
                        self.send_player_update(player_update, player_at_bay)
                        self.notify_all(f"{pod_at_bay.name} left Tokyo!")
            elif self.is_in_tokyo(p_location):
                response = self.call_and_wait(MessageType.YIELD, p_id)
                if response["yield"]:
                    self.controller.relocate(p_id, p_location, Location.OUTSIDE.value)
                    player_update = UpdateEvent(location=Location.OUTSIDE.value)
                    self.send_player_update(player_update, p_id)
                    self.notify_all(f"{pod.name} left Tokyo!")

    def call_and_wait(self, command, player_id, payload={}):
        return self.socketio.call(command, payload, to=player_id, timeout=60)

    def send_player_update(self, player_update, player_id):
        payload = {"update": player_update.to_dict()}
        self.socketio.emit(MessageType.UPDATE.value, payload, to=player_id)

    def notify_player_death(self, player_id):
        self.socketio.emit(MessageType.DEATH.value, {}, to=player_id)

    def notify_all(self, message):
        game_state = self.get_game_state().to_dict()
        payload = {"message": message, "gameState": game_state}
        self.socketio.emit(MessageType.EVENT.value, payload, to=ROOM)

    def decide_starter(self):
        players = self.player_order.copy()
        winners = []
        max_score = 0
        while len(winners) != 1:
            winners = []
            max_score = 0
            self.notify_all("Determining who starts...")
            for player_id in players:
                dices = roll_dices(6)
                num_fists = Counter(dices)[DiceSymbols.FIST.value]
                if num_fists > max_score:
                    max_score = num_fists
                    winners = [player_id]
                elif num_fists == max_score:
                    winners.append(player_id)
                time.sleep(1)

            players = winners.copy()

        starter = winners[0]
        return self.player_order.index(starter)
