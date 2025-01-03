import logging
import threading
import socket
from server_code.admin_server import AdminServer
from server_code.operator_shell import OperatorShell
from server_code.client_management import ClientManagement
from server_code.utils import setup_logging

class MainServer:
    """
    The main entry point for the PRAC2 server, managing both admin and operator roles.
    """

    def __init__(self, host="0.0.0.0", port=8080, password="mysecretpass1"):
        logging.info("[MainServer] Initializing server...")
        self.HOST = host
        self.PORT = port
        self.SERVER_PASSWORD = password
        self.client_manager = ClientManagement(self)  # Pass MainServer instance here
        self.admin_server = AdminServer(self)
        self.operator_shell = OperatorShell(self.client_manager, self)
        self.ENABLED_PLUGINS = {}
        self.BUFFER_SIZE = 4096

    def start(self):
        """
        Starts the server and launches the admin and operator shells.
        """
        setup_logging()
        logging.info(f"[MainServer] Starting server on {self.HOST}:{self.PORT}.")

        # Start the listener thread
        threading.Thread(target=self.accept_connections, daemon=True).start()

        # Launch the shells
        self.launch_shells()

        # Keep the main thread alive
        self.keep_alive()

    def accept_connections(self):
        """
        Listens for incoming client connections.
        """
        logging.info("[MainServer] Starting connection listener...")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((self.HOST, self.PORT))
                server_socket.listen()
                logging.info(f"[MainServer] Listening for connections on {self.HOST}:{self.PORT}.")

                while True:
                    conn, addr = server_socket.accept()
                    logging.info(f"[MainServer] New connection from {addr}.")
                    threading.Thread(target=self.client_manager.handle_client, args=(conn, addr), daemon=True).start()
        except Exception as e:
            logging.error(f"[MainServer] Error accepting connections: {e}")

    def launch_shells(self):
        """
        Launches the operator shell in a separate thread.
        """
        logging.info("[MainServer] Launching operator shell...")
        threading.Thread(target=self.operator_shell.launch, daemon=True).start()

    def keep_alive(self):
        """
        Keeps the main thread alive.
        """
        try:
            while True:
                pass  # Infinite loop to block the main thread
        except KeyboardInterrupt:
            logging.info("[MainServer] Received shutdown signal. Exiting...")
            self.shutdown()

    def shutdown(self):
        """
        Gracefully shuts down the server.
        """
        logging.info("[MainServer] Shutting down server.")
        exit(0)


if __name__ == "__main__":
    setup_logging()

    # Default server configuration
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 8080
    SERVER_PASSWORD = "mysecretpass1"

    logging.info("[MainServer] Starting PRAC2 server...")

    # Start the server
    server = MainServer(host=SERVER_HOST, port=SERVER_PORT, password=SERVER_PASSWORD)
    server.start()
    logging.info("[MainServer] Server is running.")