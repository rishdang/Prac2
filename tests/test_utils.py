# tests/test_utils.py
# basic test for testing server capability
import unittest
from utils import validate_ip, is_port_open, generate_banner

class TestUtils(unittest.TestCase):
    def test_validate_ip(self):
        # Valid IPv4
        self.assertTrue(validate_ip("192.168.1.1"))
        # Valid IPv6
        self.assertTrue(validate_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334"))
        # Invalid IP
        self.assertFalse(validate_ip("999.999.999.999"))
        self.assertFalse(validate_ip("not_an_ip"))
    
    def test_is_port_open(self):
        # Valid ports
        self.assertTrue(is_port_open(80))  # HTTP
        self.assertTrue(is_port_open(443))  # HTTPS
        self.assertTrue(is_port_open(65535))  # Max valid port
        self.assertTrue(is_port_open(1))  # Min valid port
        # Invalid ports
        self.assertFalse(is_port_open(0))  # Below range
        self.assertFalse(is_port_open(65536))  # Above range
        self.assertFalse(is_port_open(-1))  # Negative port
    
    def test_generate_banner(self):
        # Test banner content
        banner = generate_banner()
        self.assertEqual(banner, "Welcome to the C2 server!")

if __name__ == "__main__":
    unittest.main()