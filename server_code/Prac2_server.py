import logging
import threading
from operator_session import OperatorSession
from client_management import ClientManagement
from admin_server import AdminServer
from utils import configure_logging, get_operator_banner

class MainServer:
    """
    The main server entry point for PRAC2.
    """

    def __init__(self, host="0.0.0.0", port=8080, password="defaultpass"):
        """
        Initializes the MainServer.

        Args:
            host: The server's IP address to bind to.
            port: The server's port to bind to.
            password: The authentication password.
        """
        self.HOST = host
        self.PORT = port
        self.SERVER_PASSWORD = password
        self.BUFFER_SIZE = 1024

        # Plugin management
        self.AVAILABLE_PLUGINS = {}
        self.ENABLED_PLUGINS = {}

        # Submodules
        self.client_management = ClientManagement(self)
        self.admin_server = AdminServer(self)
        self.operator_session = OperatorSession(self)

    def start_server(self):
        """
        Starts the main server to accept client connections.
        """
        server_socket = self._create_server_socket()
        logging.info(f"Server started on {self.HOST}:{self.PORT}. Waiting for connections...")
        print(get_operator_banner())

        try:
            # Launch the operator shell
            threading.Thread(target=self.operator_session.launch_operator_shell, daemon=True).start()

            while True:
                conn, addr = server_socket.accept()
                logging.info(f"New connection from {addr}")
                threading.Thread(target=self.client_management.handle_client, args=(conn, addr)).start()
        except KeyboardInterrupt:
            logging.info("Shutting down the server...")
        except Exception as e:
            logging.error(f"Error accepting connections: {e}")
        finally:
            server_socket.close()

    def _create_server_socket(self):
        """
        Creates a server socket.

        Returns:
            socket: The configured server socket.
        """
        import socket

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.HOST, self.PORT))
        server_socket.listen(5)
        return server_socket

    def enable_plugin(self, plugin_name):
        """
        Enables a plugin dynamically.

        Args:
            plugin_name: The name of the plugin to enable.

        Returns:
            bool: True if enabled, False otherwise.
        """
        return self.admin_server.enable_plugin(plugin_name)

    def disable_plugin(self, plugin_name):
        """
        Disables a plugin dynamically.

        Args:
            plugin_name: The name of the plugin to disable.

        Returns:
            bool: True if disabled, False otherwise.
        """
        return self.admin_server.disable_plugin(plugin_name)

    def show_status(self):
        """
        Displays the server's current status.

        Returns:
            str: The server's status message.
        """
        return self.admin_server.show_status()


if __name__ == "__main__":
    configure_logging()

    # Initialize and start the server
    server = MainServer(host="0.0.0.0", port=8080, password="mysecretpass1")
    server.start_server()