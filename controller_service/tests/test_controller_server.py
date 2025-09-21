import unittest
from unittest.mock import MagicMock, patch, call
import json

from controller_service.controller_server import ControllerServer

class TestControllerServer(unittest.TestCase):

    @patch('controller_service.controller_server.KubeDao')
    @patch('controller_service.controller_server.pod_client')
    def setUp(self, mock_pod_client, mock_kube_dao):
        self.mock_kube_dao_instance = mock_kube_dao.return_value
        self.mock_pod_client = mock_pod_client
        self.server = ControllerServer()
        self.app = self.server.app.test_client()

    def test_ping(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), 'Alive')

    def test_init_game(self):
        players_data = [{'player1': 'Gigazaur'}, {'player2': 'Meka Dragon'}]
        self.mock_kube_dao_instance.create_pod.side_effect = [30000, 30001] # Mock node_port
        self.mock_kube_dao_instance.list_all_namespaces.return_value = ["outside", "tokyo-city", "tokyo-bay"]

        response = self.app.post('/initGame', json={'players': players_data})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.mock_kube_dao_instance.create_namespaces.assert_called_once()
        self.assertEqual(self.mock_kube_dao_instance.create_pod.call_count, 2)
        self.mock_kube_dao_instance.create_pod.assert_has_calls([
            call(pod_name='Gigazaur', namespace='outside', player_id='player1', service_port=33333),
            call(pod_name='Meka Dragon', namespace='outside', player_id='player2', service_port=33334),
        ], any_order=True)

        self.assertEqual(len(data['players']), 2)
        self.assertEqual(data['players'][0]['name'], 'Gigazaur')
        self.assertEqual(data['locations'], ["outside", "tokyo-city", "tokyo-bay"])

    @patch('controller_service.middleware.pod_client.update_monster_location')
    def test_destroy_tokyo_bay(self, mock_update_monster_location):

        self.mock_kube_dao_instance.list_all_pods.return_value = {'tokyo-bay': ['Gigazaur']}
        self.server.player_ids_by_name = {'Gigazaur': 'player1'}
        self.server.players_by_id = {'player1': ('Gigazaur', 'http://127.0.0.1:30000', 30000)}

        response = self.app.post('/destroyTokyoBay')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.mock_kube_dao_instance.list_all_pods.assert_called_once()
        self.mock_kube_dao_instance.move_pod.assert_called_once_with(
            pod_name='Gigazaur', from_namespace='tokyo-bay', target_namespace='outside', service_port=30000
        )
        mock_update_monster_location.assert_called_once_with(
            url='http://127.0.0.1:30000', location='outside'
        )
        self.mock_kube_dao_instance.delete_namespace.assert_called_once_with('tokyo-bay')
        self.assertEqual(data['playerId'], 'player1')

    def test_get_pod_url(self):
        self.server.players_by_id = {'player1': ('Gigazaur', 'http://127.0.0.1:30000', 30000)}
        response = self.app.post('/getPodUrl', json={'playerId': 'player1'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['podUrl'], 'http://127.0.0.1:30000')

    def test_destroy_all(self):
        response = self.app.post('/destroyAll')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.mock_kube_dao_instance.delete_all_namespaces.assert_called_once()
        self.assertEqual(data['status'], 'success')

    @patch('controller_service.middleware.pod_client.update_monster_location')
    def test_relocate(self, mock_update_monster_location):
        mock_update_monster_location.return_value = {}
        self.server.players_by_id = {'player1': ('Gigazaur', 'http://127.0.0.1:30000', 30000)}
        response = self.app.post('/relocate', json={
            'playerId': 'player1',
            'currentLocation': 'outside',
            'targetLocation': 'tokyo-city'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.mock_kube_dao_instance.move_pod.assert_called_once_with(
            'Gigazaur', from_namespace='outside', target_namespace='tokyo-city', service_port=30000
        )
        mock_update_monster_location.assert_called_once_with(
            url='http://127.0.0.1:30000', location='tokyo-city'
        )
        self.assertEqual(data['status'], 'success')

    def test_destroy_pod(self):
        self.server.players_by_id = {'player1': ('Gigazaur', 'http://127.0.0.1:30000', 30000)}
        response = self.app.post('/destroyPod', json={'playerId': 'player1', 'location': 'outside'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.mock_kube_dao_instance.delete_pod.assert_called_once_with('Gigazaur', 'outside')
        self.assertEqual(data['status'], 'success')

    def test_get_node_state(self):
        self.mock_kube_dao_instance.list_all_pods.return_value = {
            'tokyo-city': ['Gigazaur'],
            'tokyo-bay': ['Meka Dragon'],
            'outside': ['some-other-monster']
        }
        response = self.app.post('/getNodeState')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.mock_kube_dao_instance.list_all_pods.assert_called_once()
        self.assertEqual(data, {
            'tokyo-city': 'Gigazaur',
            'tokyo-bay': 'Meka Dragon',
            'outside': ['some-other-monster']
        })
