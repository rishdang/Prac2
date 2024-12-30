import unittest
from unittest.mock import patch, MagicMock
import socket
from server_code.admin_server import AdminServer

class TestAdminServer(unittest.TestCase):

    def setUp(self):
        # Mock main_server with necessary methods and attributes
        self.mock_main_server = MagicMock()
        self.mock_main_server.get_status.return_value = "Server is running."
        self.mock_main_server.list_plugins.return_value = "Plugin list."
        self.mock_main_server.client_management = MagicMock()
        self.mock_main_server.client_management.list_connections.return_value = "Client connections."

        # Initialize AdminServer instance
        self.admin_server = AdminServer(host='127.0.0.1', port=9999, main_server=self.mock_main_server)

    @patch('server_code.admin_server.socket.socket')
    def test_register_binds_to_host_and_port(self, mock_socket):
        mock_socket_instance = mock_socket.return_value
        mock_socket_instance.bind.side_effect = [None, OSError(98, 'Address already in use'), None]

        self.admin_server.register()

        # Check if bind was called with the correct host and port
        mock_socket_instance.bind.assert_any_call(('127.0.0.1', 9999))
        # Check if it tried the next port after the first was in use
        mock_socket_instance.bind.assert_any_call(('127.0.0.1', 10000))
        # Ensure listen was called
        mock_socket_instance.listen.assert_called_once()

    def test_handle_admin_command_status(self):
        response = self.admin_server._handle_admin_command('status')
        self.assertEqual(response, "Server is running.")

    def test_handle_admin_command_list(self):
        response = self.admin_server._handle_admin_command('list')
        self.assertEqual(response, "Plugin list.")

    def test_handle_admin_command_list_connections(self):
        response = self.admin_server._handle_admin_command('list connections')
        self.assertEqual(response, "Client connections.")

    def test_handle_admin_command_enable_plugin(self):
        response = self.admin_server._handle_admin_command('enable sample_plugin')
        self.mock_main_server.enable_plugin.assert_called_with('sample_plugin')
        self.assertEqual(response, "Plugin 'sample_plugin' enabled.")

    def test_handle_admin_command_disable_plugin(self):
        response = self.admin_server._handle_admin_command('disable sample_plugin')
        self.mock_main_server.disable_plugin.assert_called_with('sample_plugin')
        self.assertEqual(response, "Plugin 'sample_plugin' disabled.")

    def test_handle_admin_command_unknown(self):
        response = self.admin_server._handle_admin_command('unknown_command')
        self.assertEqual(response, "Unknown command 'unknown_command'. Type 'help' for usage.")

    @patch('server_code.admin_server.get_admin_banner', return_value="Admin Banner")
    def test_admin_session_sends_banner(self, mock_get_admin_banner):
        mock_conn = MagicMock()
        mock_conn.recv.side_effect = [b'exit\n']
        self.admin_server._admin_session(mock_conn, ('127.0.0.1', 12345))
        mock_conn.sendall.assert_any_call(b"Admin Banner")

if __name__ == '__main__':
    unittest.main()