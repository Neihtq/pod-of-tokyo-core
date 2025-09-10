from collections import Counter

from middleware.controller_client import ControllerClient
from middleware.pod_client import PodClient
from model import Commands, DiceSymbols, Location
from service.dice_service import roll_dices

WINNING_CONDITION = 20
MAX_NUM_THROWS = 3
SCORE_THRESHOLD = 3


class GameService:
    def __init__(self, socketio, controller_url):
        self.socketio = socketio
        self.players = {}
        self.player_order = []
        self.connection_ids = set()
        self.controller = ControllerClient(base_url=controller_url)

    def add(self, sid):
        self.connection_ids.add(sid)
        print(f"[+] Added player {sid}")

    def remove(self, sid):
        if sid in self.players:
            del self.players[sid]
            print(f"[-] Removed player {sid}")

    def get(self, sid):
        return self.players.get(sid)

    def all(self):
        return list(self.players.keys())

    def start_game(self):
        game_data = self.controller.init_game(self.players.keys())
        players = game_data["players"]
        for p in players:
            self.players[p[0]] = PodClient(base_url=p[1], name=p[2], player_id=p[0])
            self.player_order.append(p[0])

        self.locations = {
            game_data["locations"]["tokyoBay"]: Location.BAY,
            game_data["locations"]["tokyoCity"]: Location.CITY,
            game_data["locations"]["outside"]: Location.OUTSIDE,
        }

    def start_turn(self, player_id):
        pod = self.players[player_id]
        health, score, energy, location = pod.get_state()
        print(
            f"{pod.name}'s state: health={health}, energ={energy}, location={location}"
        )

        if (
            self.locations[location] == Location.CITY
            or self.locations[location] == Location.BAY
        ):
            pod.updateScore(1)
            score += 1

        if score == WINNING_CONDITION:
            return self.player_won(player_id)

        dices = self.reroll_dices(player_id)
        self.resolve_dices(player_id, dices, location)

        node_states = self.controller.get_node_states()
        if node_states["tokyoCity"] is None:
            self.controller.relocate(player_id, Location.CITY)
        elif len(self.players.keys()) > 3 and node_states["tokyoBay"] is None:
            self.controller.relocate(player_id, Location.BAY)

    def reroll_dices(self, player_id):
        num_throws = 6
        throw_count = 0
        dices_to_keep = []
        while throw_count < MAX_NUM_THROWS and len(dices_to_keep) < 6:
            dices = roll_dices(6)
            response = self.call_and_wait(
                Commands.ROLL_AND_RESOLVE, player_id, {"dices": dices}
            )
            dices_to_keep = response["dicesToKeep"]
            num_throws = num_throws - len(dices_to_keep)
            throw_count += 1

        return dices_to_keep

    def resolve_dices(self, pod, dices, location):
        counter = Counter(dices)
        if counter[DiceSymbols.HEART.value] > 0:
            pod.heal(life=counter[DiceSymbols.HEART.value])
        if counter[DiceSymbols.FIST.value] > 0:
            self.slap(pod.player_id, location, damage=counter[DiceSymbols.FIST.value])
        if counter[DiceSymbols.THUNDER.value] > 0:
            pod.heal(energy=counter[DiceSymbols.THUNDER.value])

        num_counter = 0
        score_count = 0
        for num in [DiceSymbols.ONE, DiceSymbols.TWO, DiceSymbols.THREE]:
            if num.value in counter:
                num_counter += 1
                score_count += int(num.value)  # type:ignore
        if score_count >= SCORE_THRESHOLD:
            pod.update_score(score=score_count)

    def slap(self, player_id, location, damage):
        player_order_copy = []
        i = 0
        while i < len(self.player_order):
            p_id = self.player_order[i]
            pod = self.players[p_id]
            player_order_copy.append(p_id)

            if p_id == player_id:
                i += 1
                continue

            health, _, _, p_location = pod.get_state()
            if p_location == location:
                i += 1
                continue

            pod.slap(damage)
            healh -= 1
            if health == 0:
                player_order_copy.pop()
                self.controller.destroy_pod(p_id)
                del self.players[p_id]
            elif location == Location.OUTSIDE and p_location in {
                Location.CITY,
                Location.BAY,
            }:
                response = self.call_and_wait(self, Commands.YIELD, p_id)
                if response["yield"]:
                    self.controller.relocate(p_id, Location.OUTSIDE)

            i += 1
        self.player_order = player_order_copy

    def player_won(self, player_id):
        print(f"Player {player_id} won!")
        pass

    def call_and_wait(self, command, player_id, payload={}):
        return self.socketio.call(command, payload, room=player_id)

    def decide_starter(self):
        return 0

    def game_loop(self):
        idx = self.decide_starter()
        while len(self.players.keys()) > 1:
            player_id = self.player_order[idx]
            self.start_turn(player_id)
