import time
import logging
from collections import Counter

from flask_socketio import SocketIO
from pod_of_tokyo_commons.constants import OUTSIDE_KEY, TOKYO_BAY_KEY, TOKYO_CITY_KEY
from pod_of_tokyo_commons.entities import DiceSymbols
from pod_of_tokyo_commons.model import Location, MessageType, PodStatus
from pod_of_tokyo_commons.model.update_event import UpdateEvent

from game_service.middleware.controller_client import ControllerClient
from game_service.middleware.pod_client import PodClient
from game_service.service.dice_service import roll_dices
from game_service.service.notification_service import NotificationService
from game_service.service.player_manager import PlayerManager
from game_service.utils import game_utils


class GameService:
    def __init__(self, socketio: SocketIO, controller_url):
        self.socketio = socketio
        self.controller = ControllerClient(controller_url=controller_url)
        self.reset()

    def reset(self):
        self.winner = None
        self.turn = 0
        self.tokyo_bay_destroyed = False


    def remove(self, sid):
        self.manager.remove_player(sid)

    def init_notifier(self):
        self.notifier = NotificationService(
            sio=self.socketio,
            manager=self.manager,
        )

    def wait_for_game_ready(self):
        logging.info("Waiting for fleet to be ready")
        ready = False
        while not ready:
            fleet_status = self.controller.get_fleet_status()
            ready = all(status == PodStatus.ACTIVE.value for status in fleet_status)
            time.sleep(2)

    def start_game(self):
        self.notifier.notify_all("Initializing game...")
        players = self.manager.get_player_list()
        game_data = self.controller.init_game(players)

        players = game_data["players"]
        for p in players:
            player_id = p["playerId"]
            self.manager.set_pod_and_add_to_order(
                player_id=player_id,
                pod_client=PodClient(
                    base_url=p["podUrl"], name=p["name"], player_id=p["playerId"]
                ),
            )
            update = UpdateEvent(location=Location.OUTSIDE, health=10)
            self.notifier.send_player_update(player_update=update, player_id=player_id)

        key_to_location_map = {
            TOKYO_CITY_KEY: Location.CITY,
            TOKYO_BAY_KEY: Location.BAY,
            OUTSIDE_KEY: Location.OUTSIDE,
        }
        self.locations = {
            location: key_to_location_map[location]
            for location in game_data["locations"]
        }
        self.tokyo_bay_destroyed = self.manager.get_num_alive()
        self.notifier.notify_game_start()
        self.wait_for_game_ready()
        self.notifier.notify_all("Game started!")

    def game_loop(self):
        while True:
            self.init_notifier()
            self.start_game()
            index = self.decide_starter()
            while not self.winner:
                player_id = self.manager.get_player_at_index(index)
                if self.manager.is_dead(player_id):
                    index += 1
                    continue

                name = self.manager.get_player_name(player_id)
                self.notifier.notify_all(f"It's {name}'s turn.")
                self.start_turn(player_id)
                index = (index + 1) % self.manager.get_number_of_players()
                self.notifier.notify_turn_end((player_id))
                self.turn += 1

            self.notifier.notify_all("Resetting game state...")
            self.controller.destroy_all()
            self.reset()

    def start_turn(self, player_id):
        logging.info(f"Beginning turn of {player_id}")
        pod = self.manager.get_pod(player_id)
        _, score, _, location_key = pod.get_state()

        location = self.locations[location_key]
        if not game_utils.is_in_tokyo(
            location_data=self.locations, location_key=location_key
        ):
            score, location_key = self.fill_empty_space(pod, score)
            if location_key:
                location = self.locations[location_key]
        else:
            pod.update_score(2)
            score += 2
            player_update = UpdateEvent(location=location, score=2)
            self.notifier.send_player_update(player_update, pod.player_id)
            self.notifier.notify_all(f"{pod.name} received 2 stars!")

        if self.check_winner(pod, score):
            return

        dices = self.reroll_dices(pod)
        self.resolve_dices(pod, dices, location)

        if location == Location.OUTSIDE:
            score, _ = self.fill_empty_space(pod, score)

        self.check_winner(pod, score)

    def fill_empty_space(self, pod, score):
        node_state = self.controller.get_node_state()
        location_key = None
        if node_state[TOKYO_CITY_KEY] is None:
            location_key = TOKYO_CITY_KEY
        elif self.manager.get_num_alive() > 4 and node_state[TOKYO_BAY_KEY] is None:
            location_key = TOKYO_BAY_KEY

        if location_key:
            location = self.locations[location_key]
            self.notifier.notify_all(f"{pod.name} enters {location.value}!")
            self.controller.relocate(pod.player_id, OUTSIDE_KEY, location_key)
            pod.update_score(1)
            score += 1
            player_update = UpdateEvent(location=location, score=1)
            self.notifier.send_player_update(player_update, pod.player_id)
            self.notifier.notify_all(f"{pod.name} received 1 star!")

        return score, location_key

    def check_winner(self, pod, score):
        is_winner = score == game_utils.WINNING_CONDITION or (
            self.manager.get_num_alive() == 1
            and not self.manager.is_dead(pod.player_id)
        )
        if is_winner:
            self.winner = pod.name
            self.notifier.notify_game_end(self.winner)
            self.notifier.notify_all(f"{pod.name} is the King of Tokyo!")

        return is_winner

    def reroll_dices(self, pod: PodClient):
        self.notifier.call_and_wait(MessageType.ROLL, pod.player_id)
        num_dices = num_throws = 6
        throw_count = 0
        max_num_throws = 3
        dices_to_keep = []
        while throw_count < max_num_throws and num_throws > 0:
            dices = roll_dices(num_throws)
            self.notifier.notify_all(f"{pod.name} threw the dices! {dices}")

            response = self.notifier.call_and_wait(
                MessageType.REROLL_AND_RESOLVE, pod.player_id, {"dices": dices}
            )
            chosen_dices = response["dices"]
            dices_to_keep.extend(chosen_dices)
            self.notifier.notify_all(f"{pod.name} kept {dices_to_keep}")
            num_throws = num_throws - len(chosen_dices)
            throw_count += 1

        logging.info(f"chosen: {chosen_dices}")
        logging.info(f"thrown: {dices}")
        if len(dices_to_keep) < num_dices:
            remaining_dices = list((Counter(dices) - Counter(chosen_dices)).elements())
            logging.info(remaining_dices)
            dices_to_keep.extend(remaining_dices)

        logging.info(f"to keep: {dices_to_keep}")
        return dices_to_keep

    def resolve_dices(self, pod, dices, location):
        self.notifier.notify_all(f"{pod.name} is resolving their dices: {dices}")
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
                self.notifier.send_player_update(player_update, pod.player_id)
                self.notifier.notify_all(f"{pod.name} charged {amount} energy.")
            elif key in DiceSymbols.NUMBERS.value and amount >= 3:
                score = int(key) + max(0, amount - 3) * int(key)
                pod.update_score(score=score)
                player_update = UpdateEvent(location=location, score=score)
                self.notifier.send_player_update(player_update, pod.player_id)
                msg_suffix = "star" if score == 1 else "stars"
                message = f"{pod.name} received {score} {msg_suffix}!"
                self.notifier.notify_all(message)

    def heal_player(self, pod, amount, location):
        if game_utils.is_in_tokyo(location_data=self.locations, location=location):
            self.notifier.notify_all(
                f"{pod.name} is in Tokyo! Healing in Tokyo is not possible!"
            )
            return
        health, _, _, _ = pod.get_state()
        if health < 10:
            amount = min(amount, 10 - health)
            pod.heal(health=amount)
            player_update = UpdateEvent(location=location, health=amount)
            self.notifier.send_player_update(player_update, pod.player_id)
            self.notifier.notify_all(f"{pod.name} healed {amount} life points.")

    def slap(self, active_pod, location, damage):
        if self.turn == 0:
            self.notifier.notify_all(
                f"The beginning player cannot slap other players on their first turn!"
            )
            return

        for p_id in self.manager.get_player_order:
            if self.manager.is_dead(p_id) or p_id == active_pod.player_id:
                continue

            pod = self.manager.get_pod(p_id)
            health, _, _, p_location = pod.get_state()
            if self.locations[p_location] == location or (
                game_utils.is_in_tokyo(location_data=self.locations, location=location)
                and game_utils.is_in_tokyo(
                    location_data=self.locations, location_key=p_location
                )
            ):
                continue

            pod.slap(damage)
            player_update = UpdateEvent(
                location=self.locations[p_location], damage=damage
            )
            self.notifier.send_player_update(player_update, p_id)
            self.notifier.notify_all(
                f"{active_pod.name} slapped {pod.name}! {pod.name} lost {damage} life points."
            )
            health -= damage
            if health <= 0:
                self.manager.add_dead_player(p_id)
                self.controller.destroy_pod(p_id, p_location)
                self.notifier.notify_death(p_id)
                self.notifier.notify_all(f"{pod.name} died!")

                if self.manager.get_num_alive() <= 4 and not self.tokyo_bay_destroyed:
                    self.destroy_tokyo_bay()

            elif game_utils.is_in_tokyo(
                location_data=self.locations, location_key=p_location
            ):
                response = self.notifier.call_and_wait(MessageType.YIELD, p_id)
                if response["isYielding"]:
                    self.notifier.notify_all(f"{pod.name} is leaving Tokyo!")
                    self.controller.relocate(p_id, p_location, OUTSIDE_KEY)
                    player_update = UpdateEvent(location=Location.OUTSIDE)
                    self.notifier.send_player_update(player_update, p_id)

            time.sleep(0.5)

    def destroy_tokyo_bay(self):
        player_id_at_bay = self.controller.destroy_tokyo_bay()["playerId"]
        self.notifier.notify_all(f"Tokyo Bay has been flooded!")
        self.tokyo_bay_destroyed = True
        if player_id_at_bay:
            pod_at_bay = self.manager.get_pod(player_id_at_bay)
            self.notifier.notify_all(f"{pod_at_bay.name} is leaving Tokyo!")
            player_update = UpdateEvent(location=Location.OUTSIDE)
            self.notifier.send_player_update(player_update, player_id_at_bay)

    def decide_starter(self):
        players = self.manager.get_player_order().copy()
        winners = []
        max_score = 0
        self.notifier.notify_all("Determining who starts...")
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

        starting_player_id = winners[0]
        return self.manager.get_player_index(starting_player_id)

    def set_players(self, name_by_id: dict[str, str]):
        self.manager = PlayerManager(name_by_id)
