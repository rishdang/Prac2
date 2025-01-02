import logging
from utils import authenticate_client
from command_handler import CommandHandler

class ClientManagement:
    """
    Manages client connections and sessions.
    """

    def __init__(self, main_server):
        """
        Initializes the ClientManagement module.

        Args:
            main_server: The main server instance.
        """
        self.main_server = main_server
        self.clients = {}  # Store active client connections
        self.command_handler = CommandHandler(main_server)

    def handle_client(self, conn, addr):
        """
        Handles a connected client, including authentication and session management.
        """
        logging.info(f"[ClientManagement] Connected by {addr}")

        if not authenticate_client(conn, self.main_server.SERVER_PASSWORD):
            logging.info("[ClientManagement] Authentication failed. Closing connection.")
            conn.close()
            return

        client_id = len(self.clients) + 1
        self.clients[client_id] = conn
        logging.info(f"[ClientManagement] Client {client_id} authenticated.")

        try:
            # Send authentication confirmation
            conn.sendall(b"REMOTE_SHELL_CONFIRMED\n")

            # Proceed to handle session
            self.handle_session(conn, client_id)
        finally:
            self.remove_client(client_id)

    def handle_session(self, conn, client_id):
        """
        Processes the client's session.
        """
        try:
            conn.sendall(b"Welcome to PRAC2!\nType 'exit' to close the connection.\n")
            while True:
                try:
                    conn.sendall(b"> ")
                    command = conn.recv(self.main_server.BUFFER_SIZE).decode(errors="replace").strip()
                    if not command:
                        logging.info(f"[ClientManagement] Client {client_id} disconnected.")
                        break
                    if command.lower() in {"exit", "quit"}:
                        conn.sendall(b"Goodbye!\n")
                        break
                    response = self.command_handler.handle_command(command)
                    conn.sendall(response.encode() + b"\n")
                except BrokenPipeError:
                    logging.warning(f"[ClientManagement] Broken pipe with client {client_id}. Disconnecting.")
                    break
                except Exception as e:
                    logging.error(f"[ClientManagement] Error during session with client {client_id}: {e}")
                    break
        finally:
            self.remove_client(client_id)

    def remove_client(self, client_id):
        """
        Removes a client from the active list.

        Args:
            client_id: The unique ID of the client to be removed.
        """
        if client_id in self.clients:
            conn = self.clients.pop(client_id)
            conn.close()
            logging.info(f"[ClientManagement] Client {client_id} disconnected.")

    def list_active_clients(self):
        """
        Lists all active client connections.

        Returns:
            list: A list of active client IDs.
        """
        return list(self.clients.keys())