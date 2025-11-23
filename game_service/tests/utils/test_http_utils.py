import unittest
from unittest.mock import patch
from game_service.utils import http_utils

class TestHttpUtils(unittest.TestCase):
    @patch("game_service.utils.http_utils.requests")
    def test_get(self, mock_requests):
        url = "http://test.com"
        resource_id = "123"
        http_utils.get(url, resource_id)
        mock_requests.get.assert_called_with("http://test.com/123")

    @patch("game_service.utils.http_utils.requests")
    def test_post(self, mock_requests):
        base_url = "http://test.com"
        endpoint = "api"
        payload = {"key": "value"}
        
        mock_response = mock_requests.post.return_value
        mock_response.json.return_value = {"status": "ok"}
        
        result = http_utils.post(base_url, endpoint, payload)
        
        mock_requests.post.assert_called_with("http://test.com/api", json=payload)
        self.assertEqual(result, {"status": "ok"})

    @patch("game_service.utils.http_utils.requests")
    def test_put(self, mock_requests):
        url = "http://test.com/123"
        payload = {"key": "value"}
        http_utils.put(url, payload)
        mock_requests.put.assert_called_with(url, json=payload)

    @patch("game_service.utils.http_utils.requests")
    def test_delete(self, mock_requests):
        url = "http://test.com/123"
        http_utils.delete(url)
        mock_requests.delete.assert_called_with(url)
