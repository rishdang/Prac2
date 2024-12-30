# basic auth tests
import unittest
from server_code.admin_server import validate_admin_credentials

class TestAdminServer(unittest.TestCase):
    def test_valid_credentials(self):
        self.assertTrue(validate_admin_credentials("admin", "secure_password"))

    def test_invalid_username(self):
        self.assertFalse(validate_admin_credentials("user", "secure_password"))

    def test_invalid_password(self):
        self.assertFalse(validate_admin_credentials("admin", "wrong_password"))

    def test_empty_credentials(self):
        self.assertFalse(validate_admin_credentials("", ""))

if __name__ == "__main__":
    unittest.main()