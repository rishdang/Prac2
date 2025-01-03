import logging
import threading
import socket
from server_code.utils import generate_client_id


class ClientManagement:
    """
    Handles client session management, including communication and shell handling.
    """

    def __init__(self, main_server):
        self.main_server = main_server
        self.clients = {}
        self.client_id_counter = 0
        self.lock = threading.Lock()

    def handle_client(self, conn, addr):
        """
        Handles an individual client session.
        """
        with self.lock:
            self.client_id_counter += 1
            numeric_id = self.client_id_counter
            connection_id = generate_client_id(addr)
            client_info = {
                "numeric_id": numeric_id,
                "connection_id": connection_id,
                "connection": conn,
                "address": addr,
                "hostname": None,
                "shell": None,
            }
            # Resolve hostname
            try:
                client_info["hostname"] = socket.gethostbyaddr(addr[0])[0]
            except Exception:
                client_info["hostname"] = "Unknown"
            self.clients[numeric_id] = client_info

        try:
            # Authenticate client
            if not self.authenticate_client(conn):
                logging.warning(f"[ClientManagement] Client {numeric_id} failed authentication.")
                self.disconnect_client(numeric_id)
                return

            # Detect shell type
            shell = self.detect_shell(conn, numeric_id)
            if not shell:
                logging.warning(f"[ClientManagement] Client {numeric_id} did not send a valid shell.")
                self.disconnect_client(numeric_id)
                return
            client_info["shell"] = shell
            logging.info(f"[ClientManagement] Client {numeric_id} is using shell: {shell}")

            # Command handling loop
            while True:
                command = conn.recv(1024).decode(errors="replace").strip()
                if not command:
                    logging.info(f"[ClientManagement] Client {numeric_id} disconnected.")
                    break
                logging.info(f"[ClientManagement] Received command from {numeric_id}: {command}")
                response = self.execute_command(conn, command, shell)
                if response:
                    conn.sendall(response.encode("utf-8"))
        except Exception as e:
            logging.error(f"[ClientManagement] Error during session with client {numeric_id}: {e}")
        finally:
            self.disconnect_client(numeric_id)

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

    def execute_command(self, conn, command, shell):
        """
        Executes a command using the detected shell and returns the output.
        """
        try:
            # Send command to the shell
            process = subprocess.Popen(
                [shell, "-c", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = process.communicate()
            return stdout if stdout else stderr
        except Exception as e:
            logging.error(f"[ClientManagement] Error executing command: {e}")
            return f"Error: {e}"

    def get_active_clients(self):
        """
        Returns a list of active clients with numeric IDs.
        """
        with self.lock:
            return {
                numeric_id: {
                    "address": client_info["address"],
                    "hostname": client_info["hostname"],
                }
                for numeric_id, client_info in self.clients.items()
            }

    def send_command_to_client(self, numeric_id, command):
        """
        Sends a command to the specified client and retrieves the response.
        """
        client = self.clients.get(numeric_id)
        if not client:
            logging.warning(f"[ClientManagement] Client {numeric_id} not found.")
            return None

        conn = client["connection"]
        try:
            conn.sendall(command.encode("utf-8"))
            response = conn.recv(4096).decode(errors="replace")
            logging.info(f"[ClientManagement] Command output from {numeric_id}: {response}")
            return response
        except Exception as e:
            logging.error(f"[ClientManagement] Error sending command to client {numeric_id}: {e}")
            return None

    def disconnect_client(self, numeric_id):
        """
        Disconnects a client and cleans up the session.
        """
        client_info = self.clients.pop(numeric_id, None)
        if client_info:
            try:
                client_info["connection"].close()
                logging.info(f"[ClientManagement] Client {numeric_id} disconnected.")
            except Exception as e:
                logging.error(f"[ClientManagement] Error disconnecting client {numeric_id}: {e}")