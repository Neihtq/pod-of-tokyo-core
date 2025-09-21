import unittest
from unittest.mock import MagicMock, patch, call, Mock
from kubernetes.client.rest import ApiException

from controller_service.kube.kube_dao import KubeDao
# Removed: from pod_of_tokyo_commons.constants import MONSTER_NAMES_SET # This import is no longer needed here

class MockPod:
    def __init__(self, namespace, name):
        self.metadata = Mock()
        self.metadata.namespace = namespace
        self.metadata.name = name

class TestKubeDao(unittest.TestCase):

    
    @patch('kubernetes.config.load_kube_config')
    @patch('kubernetes.client.CoreV1Api')
    @patch('controller_service.kube.kube_dao.subprocess.run')
    def setUp(self, mock_core_v1_api, mock_load_kube_config, mock_subprocess_run):
        self.mock_core_v1_api_class = mock_core_v1_api
        self.mock_core_v1_api = mock_core_v1_api.return_value
        self.mock_subprocess_run = mock_subprocess_run
        mock_load_kube_config.return_value = None
        with patch('controller_service.kube.kube_dao.client.CoreV1Api') as mock_client_core_v1_api:
            mock_client_core_v1_api.return_value = self.mock_core_v1_api
            self.kube_dao = KubeDao()

    @patch('controller_service.kube.kube_dao.subprocess.run')
    def test_init_minikube_start(self, mock_subprocess_run):
        # Re-initialize KubeDao to ensure __init__ is called
        self.kube_dao = KubeDao()
        mock_subprocess_run.assert_called_once_with(["minikube", "start"], check=True)

    def test_create_namespaces(self):
        location_names = ["outside", "tokyo-city", "tokyo-bay"]
        self.kube_dao.create_namespaces(location_names)
        self.assertEqual(self.mock_core_v1_api.create_namespace.call_count, 3)
        actual_calls = self.mock_core_v1_api.create_namespace.call_args_list
        expected_metadata = [
            {"name": "outside", "labels": {"location": "outside"}},
            {"name": "tokyo-city", "labels": {"location": "tokyo-city"}},
            {"name": "tokyo-bay", "labels": {"location": "tokyo-bay"}},
        ]
        for i, call_arg in enumerate(actual_calls):
            body_metadata = call_arg.kwargs["body"].metadata
            self.assertEqual(body_metadata.name, expected_metadata[i]["name"])
            self.assertEqual(body_metadata.labels, expected_metadata[i]["labels"])

    def test_delete_namespace(self):
        namespace = "test-namespace"
        self.kube_dao.delete_namespace(namespace)
        self.mock_core_v1_api.delete_namespace.assert_called_once_with(name=namespace)

    def test_list_all_namespaces(self):
        mock_pod_list = MagicMock()
        mock_pod_list.items = [
            MockPod(namespace="outside", name="Gigazaur"),
            MockPod(namespace="tokyo-city", name="Meka Dragon"),
        ]
        self.mock_core_v1_api.list_pod_for_all_namespaces.return_value = mock_pod_list
        
        # Patch MONSTER_NAMES_SET directly within the test method
        with patch('controller_service.kube.kube_dao.MONSTER_NAMES_SET', new={'Gigazaur', 'Meka Dragon'}):
            pods_by_namespaces = self.kube_dao.list_all_pods()
            self.mock_core_v1_api.list_pod_for_all_namespaces.assert_called_once()
            self.assertEqual(pods_by_namespaces, {
                "outside": ["Gigazaur"],
                "tokyo-city": ["Meka Dragon"],
            })

    def test_delete_all_namespaces(self):
        self.kube_dao.list_all_namespaces = MagicMock(return_value=["outside", "tokyo-city"])
        self.kube_dao.delete_all_namespaces()
        self.assertEqual(self.mock_core_v1_api.delete_namespace.call_count, 2)
        self.mock_core_v1_api.delete_namespace.assert_has_calls([
            call("outside"),
            call("tokyo-city"),
        ], any_order=True)

    @patch('os.environ', {'DB_NAME': 'test_db', 'DB_USER': 'test_user', 'DB_PASSWORD': 'test_password', 'SERVICE_PORT': '8080', 'PLAYER_ID': 'player1', 'MONSTER_NAME': 'test-pod'}) # Add other necessary env vars
    def test_create_pod(self):
        pod_name = "test-pod"
        namespace = "outside"
        player_id = "player1"
        service_port = 8080
        
        mock_service = MagicMock()
        mock_service.spec.ports = [MagicMock(node_port=30000)]
        self.mock_core_v1_api.create_namespaced_service.return_value = mock_service

        node_port = self.kube_dao.create_pod(pod_name, namespace, player_id, service_port)
        self.mock_core_v1_api.create_namespaced_pod.assert_called_once()
        self.mock_core_v1_api.create_namespaced_service.assert_called_once()
        self.assertEqual(node_port, 30000)

    def test_delete_pod(self):
        pod_name = "test-pod"
        namespace = "outside"
        self.kube_dao.delete_pod(pod_name, namespace)
        self.mock_core_v1_api.delete_namespaced_pod.assert_called_once_with(name=pod_name, namespace=namespace)
        self.mock_core_v1_api.delete_namespaced_service.assert_called_once_with(name=f"{pod_name}-state-service", namespace=namespace)

    def test_move_pod(self):
        pod_name = "test-pod"
        from_namespace = "outside"
        target_namespace = "tokyo-city"
        service_port = 8080

        mock_pod = MagicMock()
        mock_pod.spec.containers = [MagicMock(name="container1", image="image1", ports=[], env=[], command=[], args=[], resources={}, volume_mounts=[])]
        mock_pod.spec.volumes = []
        mock_pod.metadata.labels = {"monster-name": pod_name}
        self.mock_core_v1_api.read_namespaced_pod.return_value = mock_pod
        
        self.kube_dao.delete_pod = MagicMock()
        self.kube_dao.wait_for_pod_deletion = MagicMock()
        self.kube_dao.expose_pod_port = MagicMock(return_value=30000)
        self.kube_dao.wait_for_pod_ready = MagicMock()

        self.kube_dao.move_pod(pod_name, from_namespace, target_namespace, service_port)

        self.kube_dao.delete_pod.assert_called_once_with(pod_name, from_namespace)
        self.kube_dao.wait_for_pod_deletion.assert_called_once_with(pod_name, from_namespace)
        self.mock_core_v1_api.create_namespaced_pod.assert_called_once()
        self.kube_dao.expose_pod_port.assert_called_once_with(pod_name, target_namespace, service_port)
        self.kube_dao.wait_for_pod_ready.assert_called_once_with(pod_name, target_namespace)

    def test_wait_for_pod_deletion_success(self):
        pod_name = "test-pod"
        namespace = "test-namespace"
        
        # Simulate pod existing then being deleted
        self.mock_core_v1_api.read_namespaced_pod.side_effect = [
            MagicMock(),  # Pod exists
            ApiException(status=404) # Pod deleted
        ]
        
        self.kube_dao.wait_for_pod_deletion(pod_name, namespace, timeout=2)
        self.assertEqual(self.mock_core_v1_api.read_namespaced_pod.call_count, 2)

    def test_wait_for_pod_deletion_timeout(self):
        pod_name = "test-pod"
        namespace = "test-namespace"
        
        # Simulate pod always existing
        self.mock_core_v1_api.read_namespaced_pod.return_value = MagicMock()
        
        with self.assertRaises(TimeoutError):
            self.kube_dao.wait_for_pod_deletion(pod_name, namespace, timeout=1)
        self.assertEqual(self.mock_core_v1_api.read_namespaced_pod.call_count, 1) # Called once, then loop times out

    def test_wait_for_pod_ready_success(self):
        pod_name = "test-pod"
        namespace = "test-namespace"
        
        # Simulate pod not ready, then ready
        mock_pod_not_ready = MagicMock(status=MagicMock(phase="Pending", conditions=[]))
        mock_pod_ready = MagicMock(status=MagicMock(phase="Running", conditions=[MagicMock(type="Ready", status="True")]))
        
        self.mock_core_v1_api.read_namespaced_pod.side_effect = [
            mock_pod_not_ready,
            mock_pod_ready
        ]
        
        self.kube_dao.wait_for_pod_ready(pod_name, namespace, timeout=4) # Timeout needs to be long enough for 2 retries
        self.assertEqual(self.mock_core_v1_api.read_namespaced_pod.call_count, 2)

    def test_wait_for_pod_ready_timeout(self):
        pod_name = "test-pod"
        namespace = "test-namespace"
        
        # Simulate pod never ready
        mock_pod_not_ready = MagicMock(status=MagicMock(phase="Pending", conditions=[]))
        self.mock_core_v1_api.read_namespaced_pod.return_value = mock_pod_not_ready
        
        with self.assertRaises(TimeoutError):
            self.kube_dao.wait_for_pod_ready(pod_name, namespace, timeout=1)
        self.assertEqual(self.mock_core_v1_api.read_namespaced_pod.call_count, 1) # Called once, then loop times out

if __name__ == '__main__':
    unittest.main()