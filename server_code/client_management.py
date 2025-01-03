import logging
import threading
import socket
from server_code.utils import generate_client_id


class ClientManagement:
    """
    Handles client session management, including communication and shell handling.
    """

    def __init__(self, main_server):
        self.main_server = main_server  # Store a reference to MainServer
        self.clients = {}
        self.client_id_counter = 0
        self.lock = threading.Lock()

    def handle_client(self, conn, addr):
        """
        Handles an individual client session with enhanced reliability.
        """
        with self.lock:
            self.client_id_counter += 1
            numeric_id = self.client_id_counter
            client_id = generate_client_id(addr)
            client_info = {
                "numeric_id": numeric_id,
                "connection": conn,
                "address": addr,
                "hostname": None,
                "shell": None,
            }
            try:
                client_info["hostname"] = socket.gethostbyaddr(addr[0])[0]
            except Exception:
                client_info["hostname"] = "Unknown"
            self.clients[numeric_id] = client_info

        try:
            self.initialize_session(numeric_id, conn)
            shell = self.clients[numeric_id]["shell"]
            if not shell:
                return  # Disconnect if no valid shell is detected

            # Command handling loop with proper termination detection
            while True:
                try:
                    command = self.receive_data(conn)
                    if command == "exit":
                        logging.info(f"[ClientManagement] Client {numeric_id} requested to exit.")
                        break

                    logging.info(f"[ClientManagement] Received command from {numeric_id}: {command}")
                    self.send_command_to_client(numeric_id, command)
                except socket.timeout:
                    logging.warning(f"[ClientManagement] Timeout for client {numeric_id}.")
                    break
                except Exception as e:
                    logging.error(f"[ClientManagement] Error handling client {numeric_id}: {e}")
                    break

        finally:
            self.disconnect_client(numeric_id)

    def initialize_session(self, numeric_id, conn):
        """
        Initializes the client session, including authentication and shell detection.
        """
        # Authenticate the client
        if not self.authenticate_client(conn):
            logging.warning(f"[ClientManagement] Client {numeric_id} failed authentication.")
            self.disconnect_client(numeric_id)
            return

        # Detect the client shell
        shell = self.detect_shell(conn, numeric_id)
        if shell:
            self.clients[numeric_id]["shell"] = shell
            logging.info(f"[ClientManagement] Client {numeric_id} supports shell: {shell}")
        else:
            logging.warning(f"[ClientManagement] Client {numeric_id} did not send a valid shell.")
            self.disconnect_client(numeric_id)  # Disconnect on invalid shell

    def authenticate_client(self, conn):
        """
        Authenticates a client connection using the shared server password.
        """
        try:
            # Receive password from client
            password = conn.recv(self.main_server.BUFFER_SIZE).decode(errors="replace").strip()
            if password == self.main_server.SERVER_PASSWORD:
                conn.sendall(b"REMOTE_SHELL_CONFIRMED\n")
                logging.info("[ClientManagement] Client authenticated successfully.")
                return True
            else:
                conn.sendall(b"AUTHENTICATION_FAILED\n")
                logging.warning("[ClientManagement] Client failed authentication.")
                return False
        except Exception as e:
            logging.error(f"[ClientManagement] Authentication error: {e}")
            return False

    def detect_shell(self, conn, numeric_id):
        """
        Detects the shell type reported by the client.
        """
        try:
            shell = conn.recv(self.main_server.BUFFER_SIZE).decode(errors="replace").strip()
            if shell.startswith("/bin/"):
                logging.info(f"[ClientManagement] Client {numeric_id} is using shell: {shell}")
                return shell
            else:
                logging.warning(f"[ClientManagement] Client {numeric_id} did not send a valid shell.")
                conn.sendall(b"Invalid shell type\n")
                return None
        except Exception as e:
            logging.error(f"[ClientManagement] Shell detection error for client {numeric_id}: {e}")
            return None

    def send_command_to_client(self, numeric_id, command):
        """
        Sends a command to the client and retrieves the response with reliability.
        """
        with self.lock:
            client = self.clients.get(numeric_id)
        if not client:
            logging.warning(f"[ClientManagement] Client {numeric_id} not found.")
            return None

        conn = client["connection"]
        try:
            conn.sendall(command.encode("utf-8"))
            response = self.receive_response(conn)
            logging.info(f"[ClientManagement] Command output from {numeric_id}: {response}")
            return response
        except Exception as e:
            logging.error(f"[ClientManagement] Error sending command to client {numeric_id}: {e}")
            return None

    def receive_data(self, conn):
        """
        Receives data from the client with enhanced reliability and buffering.
        """
        buffer = []
        while True:
            chunk = conn.recv(self.main_server.BUFFER_SIZE).decode(errors="replace")
            if not chunk:
                raise ConnectionError("Client disconnected.")
            buffer.append(chunk)
            if "[END_OF_RESPONSE]" in chunk:
                break
        return "".join(buffer).replace("[END_OF_RESPONSE]", "").strip()


    def receive_response(self, conn):
        """
        Receives a response from the client with enhanced buffering.
        """
        return self.receive_data(conn)

    def get_active_clients(self):
        """
        Returns a list of active clients with numeric IDs.
        """
        with self.lock:
            return {
                client_info["numeric_id"]: {
                    "address": client_info["address"],
                    "hostname": client_info["hostname"]
                }
                for client_info in self.clients.values()
            }

    def client_exists(self, numeric_id):
        """
        Checks if a client with the given numeric ID exists.
        """
        with self.lock:
            return numeric_id in self.clients

    def disconnect_client(self, numeric_id):
        """
        Disconnects a client and cleans up the session.
        """
        with self.lock:
            client_info = self.clients.pop(numeric_id, None)

        if client_info:
            try:
                client_info["connection"].close()
                logging.info(f"[ClientManagement] Client {numeric_id} disconnected.")
            except Exception as e:
                logging.error(f"[ClientManagement] Error disconnecting client {numeric_id}: {e}")