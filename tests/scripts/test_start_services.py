import unittest
from unittest.mock import patch, MagicMock
import signal
import sys
import subprocess
import start_services

class TestStartServices(unittest.TestCase):
    @patch("subprocess.Popen")
    @patch("signal.signal")
    def test_main_starts_processes(self, mock_signal, mock_popen):
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        
        mock_process.wait.side_effect = KeyboardInterrupt
        
        with self.assertRaises(SystemExit):
            start_services.main()
            
        self.assertEqual(mock_popen.call_count, 2)
        expected_calls = [
            unittest.mock.call([sys.executable, "-m", "controller_service.main"]),
            unittest.mock.call([sys.executable, "-m", "game_service.main"])
        ]
        mock_popen.assert_has_calls(expected_calls, any_order=True)
        
        mock_signal.assert_called_with(signal.SIGINT, unittest.mock.ANY)
        
        self.assertEqual(mock_process.terminate.call_count, 2)
        
    @patch("subprocess.Popen")
    def test_signal_handler(self, mock_popen):
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        
        pass
