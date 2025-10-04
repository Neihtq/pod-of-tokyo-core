import unittest

import pytest
from werkzeug.exceptions import NotFound

from game_service.entities.player import Player
from game_service.service.player_manager import PlayerManager
from middleware.pod_client import PodClient


class TestPlayerManager(unittest.TestCase):
    def setUp(self):
        self.player_manager = PlayerManager({"id": "name"})

    def test_init_player_manager(self):
        player_name_by_id = {"id": "name"}
        self.assertEqual(self.player_manager.player_name_by_id, player_name_by_id)

    def test_set_pod_succeeds(self):
        player_id = "id"
        pod_client = PodClient(
            base_url="some-url", name="some-name", player_id="some-id"
        )

        self.player_manager.set_pod(player_id=player_id, pod_client=pod_client)

        self.assertIn(player_id, self.player_manager.pod_by_player_id)
        self.assertEqual(self.player_manager.pod_by_player_id[player_id], pod_client)

    def test_set_pod_fails_when_id_does_not_exist(self):
        with pytest.raises(NotFound) as exc:
            player_id = "fake-id"
            pod_client = PodClient(
                base_url="some-url", name="some-name", player_id="some-id"
            )
            self.player_manager.set_pod(player_id=player_id, pod_client=pod_client)

        exc.match("404 Not Found: Player with id 'fake-id' does not exist")

    def test_validate_player_id(self):
        with pytest.raises(NotFound) as exc:
            player_id = "fake-id"
            self.player_manager.__validate_player_id__(player_id)

        exc.match("404 Not Found: Player with id 'fake-id' does not exist")

        with pytest.raises(NotFound) as exc:
            player_id = "id"
            self.player_manager.__validate_player_id__(player_id)

        exc.match("404 Not Found: Player with id 'id' does not have a pod")

    def test_add_to_order_succeeds(self):
        player_id = "id"
        pod_client = PodClient(
            base_url="some-url", name="some-name", player_id="some-id"
        )
        self.player_manager.set_pod(player_id=player_id, pod_client=pod_client)

        self.player_manager.add_to_order(player_id)

        self.assertIn(player_id, self.player_manager.player_order)

    def test_set_pod_and_add_to_order_succeeds(self):
        player_id = "id"
        pod_client = PodClient(
            base_url="some-url", name="some-name", player_id="some-id"
        )

        self.player_manager.set_pod_and_add_to_order(
            player_id=player_id, pod_client=pod_client
        )

        self.assertIn(player_id, self.player_manager.pod_by_player_id)
        self.assertEqual(self.player_manager.pod_by_player_id[player_id], pod_client)
        self.assertIn(player_id, self.player_manager.player_order)

    def test_add_dead_player_succeeds(self):
        player_id = "id"
        pod_client = PodClient(
            base_url="some-url", name="some-name", player_id="some-id"
        )
        self.player_manager.set_pod_and_add_to_order(
            player_id=player_id, pod_client=pod_client
        )

        self.player_manager.add_dead_player(player_id)

        self.assertIn(player_id, self.player_manager.dead_players)

    def test_is_dead(self):
        player_id = "id"
        pod_client = PodClient(
            base_url="some-url", name="some-name", player_id="some-id"
        )
        self.player_manager.set_pod_and_add_to_order(
            player_id=player_id, pod_client=pod_client
        )

        self.assertFalse(self.player_manager.is_dead(player_id))

        self.player_manager.add_dead_player(player_id)
        self.assertTrue(self.player_manager.is_dead(player_id))

    def test_remove_player_succeeds_for_existing_player(self):
        player_id = "id"
        pod_client = PodClient(
            base_url="some-url", name="some-name", player_id="some-id"
        )
        self.player_manager.set_pod(player_id=player_id, pod_client=pod_client)

        self.player_manager.remove_player(player_id)

        self.assertNotIn(player_id, self.player_manager.pod_by_player_id)

    def test_remove_player_succeeds_for_non_existing_player(self):
        player_id = "non-existing-id"

        self.player_manager.remove_player(player_id)

        self.assertNotIn(player_id, self.player_manager.pod_by_player_id)

    def test_get_player_list(self):
        expected_player_list = [Player("id", "name")]
        self.assertEqual(self.player_manager.get_player_list(), expected_player_list)

    def test_get_pod_succeeds(self):
        player_id = "id"
        pod_client = PodClient(
            base_url="some-url", name="some-name", player_id="some-id"
        )

        self.player_manager.set_pod_and_add_to_order(
            player_id=player_id, pod_client=pod_client
        )

        self.assertEqual(self.player_manager.get_pod(player_id), pod_client)

    def test_get_player_order(self):
        expected_player_order = []
        self.assertEqual(self.player_manager.get_player_order(), expected_player_order)

        player_id = "id"
        pod_client = PodClient(
            base_url="some-url", name="some-name", player_id="some-id"
        )
        self.player_manager.set_pod_and_add_to_order(
            player_id=player_id, pod_client=pod_client
        )

        expected_player_order = [player_id]
        self.assertEqual(self.player_manager.get_player_order(), expected_player_order)

    def test_get_num_alive(self):
        expected_number = 0
        self.assertEqual(self.player_manager.get_num_alive(), expected_number)

        player_id = "id"
        pod_client = PodClient(
            base_url="some-url", name="some-name", player_id="some-id"
        )
        self.player_manager.set_pod_and_add_to_order(
            player_id=player_id, pod_client=pod_client
        )
        expected_number = 1
        self.assertEqual(self.player_manager.get_num_alive(), expected_number)

    def test_get_player_name(self):
        player_id = "id"
        pod_client = PodClient(
            base_url="some-url", name="some-name", player_id="some-id"
        )
        self.player_manager.set_pod_and_add_to_order(
            player_id=player_id, pod_client=pod_client
        )

        result = self.player_manager.get_player_name(player_id)

        expected_name = "some-name"
        self.assertEqual(result, expected_name)

    def test_get_player_at_index(self):
        player_id = "id"
        pod_client = PodClient(
            base_url="some-url", name="some-name", player_id="some-id"
        )
        self.player_manager.set_pod_and_add_to_order(
            player_id=player_id, pod_client=pod_client
        )

        index = 0
        result = self.player_manager.get_player_at_index(index)

        expected_id = player_id
        self.assertEqual(result, expected_id)

    def test_get_number_of_players(self):
        expected_length = 0
        result = self.player_manager.get_number_of_players()
        self.assertEqual(expected_length, result)

        player_id = "id"
        pod_client = PodClient(
            base_url="some-url", name="some-name", player_id="some-id"
        )
        self.player_manager.set_pod_and_add_to_order(
            player_id=player_id, pod_client=pod_client
        )

        expected_length = 1
        result = self.player_manager.get_number_of_players()
        self.assertEqual(expected_length, result)

    def test_get_player_index(self):
        player_id = "id"
        pod_client = PodClient(
            base_url="some-url", name="some-name", player_id="some-id"
        )
        self.player_manager.set_pod_and_add_to_order(
            player_id=player_id, pod_client=pod_client
        )

        result = self.player_manager.get_player_index(player_id)

        expected_index = 0
        self.assertEqual(result, expected_index)
