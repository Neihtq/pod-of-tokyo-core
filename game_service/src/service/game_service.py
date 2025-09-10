from collections import Counter

from flask_socketio import join_room
from middleware.controller_client import ControllerClient
from middleware.pod_client import PodClient
from model import Commands, DiceSymbols, Location
from service.dice_service import roll_dices

WINNING_CONDITION = 20

ROOM = "king-of-tokyo"


class GameService:
    def __init__(self, socketio, controller_url):
        self.socketio = socketio
        self.players = {}
        self.player_order = []
        self.dead = set()
        self.connection_ids = set()
        self.controller = ControllerClient(base_url=controller_url)
        self.winner = None
        self.num_players_alive = 0

    def add(self, sid):
        self.connection_ids.add(sid)
        join_room(ROOM, sid=sid)
        self.players[sid] = None
        print(f"[+] Added player {sid}")

    def remove(self, sid):
        if sid in self.players:
            del self.players[sid]
            print(f"[-] Removed player {sid}")

    def start_game(self):
        game_data = self.controller.init_game(self.players.keys())
        players = game_data["players"]
        for p in players:
            self.players[p[0]] = PodClient(base_url=p[1], name=p[2], player_id=p[0])
            self.player_order.append(p[0])

        self.num_players_alive = len(self.player_order)
        self.locations = {
            game_data["locations"]["tokyoBay"]: Location.BAY,
            game_data["locations"]["tokyoCity"]: Location.CITY,
            game_data["locations"]["outside"]: Location.OUTSIDE,
        }

    def game_loop(self):
        self.start_game()
        idx = self.decide_starter()
        while not self.winner:
            player_id = self.player_order[idx]
            if player_id in self.dead:
                idx += 1
                continue

            name = self.players[player_id].name
            self.notify_all(
                Commands.MESSAGE,
                {"message": f"It's {name}'s turn."},
            )
            self.start_turn(player_id)
            idx = (idx + 1) % len(self.player_order)

    def start_turn(self, player_id):
        pod = self.players[player_id]
        _, score, _, location = pod.get_state()

        node_states = self.controller.get_node_states()
        if node_states["tokyoCity"] is None:
            self.controller.relocate(player_id, Location.CITY)
            self.notify_all(
                Commands.MESSAGE, {"message": f"{pod.name} has conquered Tokyo City!"}
            )
        elif self.num_players_alive > 4 and node_states["tokyoBay"] is None:
            self.controller.relocate(player_id, Location.BAY)
            self.notify_all(
                Commands.MESSAGE, {"message": f"{pod.name} has conquered Tokyo Bay!"}
            )

        if (
            self.locations[location] == Location.CITY
            or self.locations[location] == Location.BAY
        ):
            pod.update_score(1)
            score += 1
            self.notify_all(
                Commands.MESSAGE,
                {"message": f"{pod.name} received 1 star!"},
            )

        if self.check_winner(pod, score):
            return

        dices = self.reroll_dices(pod)
        self.resolve_dices(pod, dices, location)

        self.check_winner(pod, score)

    def check_winner(self, pod, score):
        is_winner = score == WINNING_CONDITION or (
            len(self.player_order) - len(self.dead) == 1
            and pod.player_id not in self.dead
        )
        if is_winner:
            self.winner = pod.name
            self.notify_all(
                Commands.MESSAGE,
                {"message": f"{pod.name} is the King of Tokyo!"},
            )

        return is_winner

    def reroll_dices(self, pod):
        num_throws = 6
        throw_count = 0
        dices_to_keep = []
        max_num_throws = 3
        while throw_count < max_num_throws and num_throws > 0:
            dices = roll_dices(num_throws)
            self.notify_all(
                Commands.MESSAGE, {"message": f"{pod.name} threw the dices! {dices}"}
            )

            response = self.call_and_wait(
                Commands.ROLL_AND_RESOLVE, pod.player_id, {"dices": dices}
            )
            chosen_dices = response["dicesToKeep"]
            dices_to_keep.extend(chosen_dices)
            self.notify_all(
                Commands.MESSAGE, {"message": f"{pod.name} kept {dices_to_keep}"}
            )
            num_throws = num_throws - len(chosen_dices)
            throw_count += 1

        return dices_to_keep

    def resolve_dices(self, pod, dices, location):
        counter = Counter(dices)
        for key in counter:
            amount = counter[key]
            if key == DiceSymbols.HEART.value:
                pod.heal(life=amount)
                self.notify_all(
                    Commands.MESSAGE,
                    {"message": f"{pod.name} healed {amount} life points."},
                )
            if key == DiceSymbols.FIST.value:
                self.slap(pod, location, damage=amount)

            if key == DiceSymbols.THUNDER.value:
                pod.charge_energy(energy=amount)

        num_counter = 0
        score = 0
        score_threshold = 3
        for num in [DiceSymbols.ONE, DiceSymbols.TWO, DiceSymbols.THREE]:
            if num.value in counter:
                num_counter += 1
                score += int(num.value)  # type:ignore
        if num_counter >= score_threshold:
            pod.update_score(score=score)
            msg_suffix = "star" if score == 1 else "stars"
            message = f"{pod.name} received {score} {msg_suffix}!"
            self.notify_all(
                Commands.MESSAGE,
                {"message": message},
            )

    def slap(self, active_pod, location, damage):
        for p_id in self.player_order:
            if p_id in self.dead or p_id == active_pod.player_id:
                continue

            pod = self.players[p_id]
            health, _, _, p_location = pod.get_state()
            if p_location == location:
                continue

            pod.slap(damage)
            self.notify_all(
                Commands.MESSAGE,
                {
                    "message": f"{active_pod.name} slapped {pod.name}! {pod.name} lost {damage} life points."
                },
            )
            health -= damage
            if health <= 0:
                self.dead.add(p_id)
                self.num_players_alive -= 1
                self.controller.destroy_pod(p_id)
                self.notify_all(Commands.MESSAGE, {"message": f"{pod.name} died!"})

                if self.num_players_alive <= 4:
                    player_at_bay = self.controller.destroy_tokyo_bay()["playerId"]
                    self.notify_all(
                        Commands.MESSAGE, {"message": f"Tokyo Bay has been flooded!"}
                    )
                    if player_at_bay:
                        pod_at_bay = self.players[player_at_bay]
                        self.notify_all(
                            Commands.MESSAGE,
                            {"message": f"{pod_at_bay.name} left Tokyo!"},
                        )

            elif location == Location.OUTSIDE and p_location in {
                Location.CITY,
                Location.BAY,
            }:
                response = self.call_and_wait(Commands.YIELD, p_id)
                if response["yield"]:
                    self.controller.relocate(p_id, Location.OUTSIDE)
                    self.notify_all(
                        Commands.MESSAGE,
                        {"message": f"{pod.name} left Tokyo!"},
                    )

    def call_and_wait(self, command, player_id, payload={}):
        return self.socketio.call(command, payload, to=player_id, timeout=180)

    def notify_all(self, event, payload):
        print(payload["message"])
        self.socketio.emit(event, payload, to=ROOM)

    def decide_starter(self):
        players = self.player_order.copy()
        winners = []
        max_score = 0
        while len(winners) != 1:
            self.notify_all(
                Commands.MESSAGE,
                {"message": "Determining who starts..."},
            )
            for player_id in players:
                dices = roll_dices(6)
                num_fists = Counter(dices)[DiceSymbols.FIST.value]
                if num_fists > max_score:
                    max_score = num_fists
                    winners = [player_id]
                elif num_fists == max_score:
                    winners.append(player_id)

            players = winners.copy()
            winners = []
            max_score = 0

        starter = winners[0]
        return self.player_order.index(starter)
