import unittest
from unittest.mock import MagicMock, patch

from game_service.utils import http_utils


class TestHttpUtils(unittest.TestCase):

    def test_join(self):
        self.assertEqual(
            http_utils.join("http://base.com", "endpoint"), "http://base.com/endpoint"
        )
        self.assertEqual(
            http_utils.join("http://base.com/", "endpoint"), "http://base.com/endpoint"
        )

    @patch("requests.get")
    def test_get(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        response = http_utils.get("http://base.com", "resource/1")
        mock_get.assert_called_once_with("http://base.com/resource/1")
        self.assertEqual(response, mock_response)

    @patch("requests.post")
    def test_post(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        response = http_utils.post("http://base.com", "endpoint", {"key": "value"})
        mock_post.assert_called_once_with(
            "http://base.com/endpoint", json={"key": "value"}
        )
        self.assertEqual(response, {"status": "success"})

    @patch("requests.put")
    def test_put(self, mock_put):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        response = http_utils.put("http://base.com/resource/1", {"key": "value"})
        mock_put.assert_called_once_with(
            "http://base.com/resource/1", json={"key": "value"}
        )
        self.assertEqual(response, mock_response)

    @patch("requests.delete")
    def test_delete(self, mock_delete):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        response = http_utils.delete("http://base.com/resource/1")
        mock_delete.assert_called_once_with("http://base.com/resource/1")
        self.assertEqual(response, mock_response)
