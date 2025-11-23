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

    def test_post(self):
        with patch("game_service.utils.http_utils.requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"key": "value"}
            response = http_utils.post("http://base", "endpoint", {"data": 1})
            mock_post.assert_called_with("http://base/endpoint", json={"data": 1})
            self.assertEqual(response, {"key": "value"})

    def test_post_with_none_payload(self):
        with patch("game_service.utils.http_utils.requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"key": "value"}
            response = http_utils.post("http://base", "endpoint", None)
            mock_post.assert_called_with("http://base/endpoint", json={})
            self.assertEqual(response, {"key": "value"})

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
