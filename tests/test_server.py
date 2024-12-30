# basic auth tests
import unittest
from server import authenticate_client

class TestServer(unittest.TestCase):
    def test_authenticate_client(self):
        # Mock client socket response
        mock_client = type('MockSocket', (object,), {"recv": lambda _: b"REMOTE_SHELL_CONFIRMED\n"})
        self.assertTrue(authenticate_client(mock_client))

    def test_authenticate_client_fail(self):
        mock_client = type('MockSocket', (object,), {"recv": lambda _: b"AUTH_FAILED\n"})
        self.assertFalse(authenticate_client(mock_client))

if __name__ == "__main__":
    unittest.main()