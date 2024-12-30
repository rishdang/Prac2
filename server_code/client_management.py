import logging
import threading
import socket
import time
from server_code.banner import get_operator_banner


class ClientManagement:
    """
    Manages client connections and an Operator Shell on port 20022.
    This is *not* stored in ENABLED_PLUGINS. It's a core module that MainServer calls.
    """

    def __init__(self, main_server):
        self.main_server = main_server
        self.connections = {}  # connection_id -> (conn, addr)
        self.next_id = 1
        self.active_connection_id = None
        self.lock = threading.Lock()

        # Operator shell
        self.operator_socket = None
        self.running_shell = False
        self.operator_shell_port = 20022
        self.operator_connections = 0

        # Refresh thread
        self.refresh_thread = threading.Thread(target=self._refresh_connections_loop, daemon=True)
        self.refresh_running = False

    def register(self, server_socket):
        """
        Perform setup upon creation.
        """
        logging.info("[ClientManagement] Operator shell will be launched.")
        self.launch_operator_shell()
        self.start_refresh_loop()
        return server_socket

    def unregister(self, server_socket):
        """
        Perform cleanup if needed, stopping the operator shell.
        """
        logging.info("[ClientManagement] Stopping operator shell.")
        self.stop_operator_shell()
        self.stop_refresh_loop()
        return server_socket

    # --------------------- CLIENT SESSIONS ---------------------

    def on_connection_accepted(self, conn, addr):
        with self.lock:
            conn_id = self.next_id
            self.next_id += 1
            self.connections[conn_id] = (conn, addr)
            logging.info(f"[ClientManagement] Connection #{conn_id} from {addr}")
            if self.active_connection_id is None:
                self.active_connection_id = conn_id

    def list_connections(self) -> str:
        """
        Lists active client connections.
        """
        with self.lock:
            if not self.connections:
                return "No active client connections."

            lines = []
            for cid, (conn, addr) in self.connections.items():
                active_marker = " (ACTIVE)" if cid == self.active_connection_id else ""
                lines.append(f"#{cid} -> {addr}{active_marker}")

            return "\n".join(lines)

    def refresh_connections(self):
        """
        Refreshes the connections list by checking for dead connections.
        """
        with self.lock:
            to_remove = []
            for cid, (conn, _) in self.connections.items():
                try:
                    conn.send(b"")  # Send empty packet to check connection
                except:
                    to_remove.append(cid)

            for cid in to_remove:
                self.close_connection(cid)
                logging.info(f"[ClientManagement] Removed stale connection #{cid}")

    def _refresh_connections_loop(self):
        """
        Background thread to refresh client connections every 10 seconds.
        """
        self.refresh_running = True
        while self.refresh_running:
            self.refresh_connections()
            time.sleep(10)

    def start_refresh_loop(self):
        """
        Starts the refresh loop in a separate thread.
        """
        if not self.refresh_thread.is_alive():
            self.refresh_thread = threading.Thread(target=self._refresh_connections_loop, daemon=True)
            self.refresh_thread.start()

    def stop_refresh_loop(self):
        """
        Stops the refresh loop.
        """
        self.refresh_running = False

    def terminate_connection(self, cid: int) -> str:
        """
        Terminates a client connection forcefully.
        """
        with self.lock:
            if cid not in self.connections:
                return f"No connection #{cid} found."
            conn, addr = self.connections[cid]
            try:
                conn.close()
                logging.info(f"[ClientManagement] Terminated connection #{cid} from {addr}.")
            except Exception as e:
                logging.error(f"[ClientManagement] Error while terminating connection #{cid}: {e}")
            finally:
                del self.connections[cid]
                if self.active_connection_id == cid:
                    self.active_connection_id = None
            return f"Connection #{cid} terminated."

    def switch_connection(self, new_id: int) -> str:
        """
        Switches the active client connection to a new client ID.
        """
        with self.lock:
            if new_id in self.connections:
                self.active_connection_id = new_id
                return f"Switched to connection #{new_id}."
            else:
                return f"Connection #{new_id} does not exist."

    def close_connection(self, cid: int) -> str:
        """
        Closes a client connection and removes it from the list of active connections.
        """
        with self.lock:
            if cid not in self.connections:
                return f"No connection #{cid} found."
            conn, addr = self.connections[cid]
            try:
                conn.close()
            except:
                pass
            del self.connections[cid]
            logging.info(f"[ClientManagement] Closed connection #{cid} from {addr}.")
            if self.active_connection_id == cid:
                self.active_connection_id = None
            return f"Connection #{cid} closed."

    def _run_on_active_client(self, command: str) -> str:
        """
        Sends a command to the active client and receives its output in real-time.
        """
        with self.lock:
            if not self.active_connection_id:
                return "No active client connection. Use 'connect <id>' first."

            conn, addr = self.connections[self.active_connection_id]
            try:
                # Send the command to the active client
                conn.sendall(command.encode())

                # Receive and process output in real-time
                output = []
                while True:
                    response = conn.recv(self.main_server.BUFFER_SIZE).decode(errors="replace")
                    if not response:
                        logging.warning(f"[ClientManagement] Client #{self.active_connection_id} disconnected.")
                        self.close_connection(self.active_connection_id)
                        return f"Client #{self.active_connection_id} disconnected."
                    if "[END_OF_OUTPUT]" in response:
                        output.append(response.replace("[END_OF_OUTPUT]", "").strip())
                        break
                    output.append(response.strip())

                return "\n".join(output)
            except Exception as e:
                logging.error(f"[ClientManagement] Error communicating with client #{self.active_connection_id}: {e}")
                self.close_connection(self.active_connection_id)
                return f"Error communicating with client #{self.active_connection_id}."

    # -------------------- OPERATOR SHELL --------------------

    def launch_operator_shell(self):
        """
        Launches the operator shell on the specified port.
        """
        if self.running_shell:
            logging.info("[ClientManagement] Operator shell is already running.")
            return

        self.running_shell = True
        try:
            self.operator_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.operator_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.operator_socket.bind((self.main_server.HOST, self.operator_shell_port))
            self.operator_socket.listen()
            logging.info(f"[ClientManagement] Operator shell launched on {self.main_server.HOST}:{self.operator_shell_port}")

            threading.Thread(target=self._operator_accept_loop, daemon=True).start()
        except Exception as e:
            self.running_shell = False
            logging.error(f"[ClientManagement] Failed to start operator shell: {e}")

    def stop_operator_shell(self):
        """
        Stops the operator shell.
        """
        self.running_shell = False
        if self.operator_socket:
            try:
                self.operator_socket.close()
                logging.info("[ClientManagement] Operator shell stopped.")
            except Exception as e:
                logging.error(f"[ClientManagement] Error while stopping operator shell: {e}")

    def _operator_accept_loop(self):
        """
        Accepts incoming operator connections and starts an operator session.
        """
        logging.info("[ClientManagement] Waiting for operator connections...")
        while self.running_shell:
            try:
                conn, addr = self.operator_socket.accept()
                self.operator_connections += 1
                logging.info(f"[ClientManagement] Operator connected from {addr}")
                threading.Thread(target=self._operator_session, args=(conn, addr), daemon=True).start()
            except Exception as e:
                logging.error(f"[ClientManagement] Error accepting operator connection: {e}")

    def _operator_session(self, conn, addr):
        """
        Handles the operator session, processing commands interactively.
        """
        try:
            conn.sendall(get_operator_banner().encode())
            conn.sendall(b"\nOperator Shell Ready. Type 'help' for commands.\n")
            while self.running_shell:
                conn.sendall(b"operator> ")
                line = conn.recv(self.main_server.BUFFER_SIZE).decode(errors="replace").strip()
                if not line:
                    continue
                response = self._handle_operator_command(line)
                if response:
                    conn.sendall(response.encode() + b"\n")
        except Exception as e:
            logging.error(f"[ClientManagement] Operator session error with {addr}: {e}")
        finally:
            self.operator_connections -= 1
            conn.close()
            logging.info(f"[ClientManagement] Operator session closed for {addr}")

    def _handle_operator_command(self, line: str) -> str:
        """
        Handles operator commands entered in the operator shell.
        """
        parts = line.split()
        if not parts:
            return ""

        cmd = parts[0].lower()

        if cmd in ("help", "?"):
            return (
                "Operator Shell Commands:\n"
                "  help / ?               - This help.\n"
                "  list                   - List connected clients.\n"
                "  list refresh           - Refresh the client connections.\n"
                "  connect <id>           - Switch active client session.\n"
                "  run <command>          - Run a command on the ACTIVE client.\n"
                "  close <id>             - Close a client connection by ID.\n"
                "  terminate <id>         - Terminate a client connection by ID.\n"
                "  exit / quit            - Exit operator shell.\n"
            )
        elif cmd == "list":
            if len(parts) == 2 and parts[1].lower() == "refresh":
                self.refresh_connections()
                return "Connections refreshed."
            return self.list_connections()
        elif cmd == "connect" and len(parts) == 2:
            try:
                client_id = int(parts[1])
                return self.switch_connection(client_id)
            except ValueError:
                return "Usage: connect <integer_client_id>"
        elif cmd == "terminate" and len(parts) == 2:
            try:
                cid = int(parts[1])
                return self.terminate_connection(cid)
            except ValueError:
                return "Usage: terminate <integer_client_id>"
        elif cmd == "run":
            if not self.active_connection_id:
                return "No active client connection. Use 'connect <id>' first."
            if len(parts) < 2:
                return "Usage: run <command>"
            command = " ".join(parts[1:])
            return self._run_on_active_client(command)
        elif cmd in ("exit", "quit"):
            self.stop_operator_shell()
            return "Operator shell exited."
        else:
            return f"Unknown command: {line}"