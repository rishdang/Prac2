# server_code/admin_server.py

import socket
import logging
import threading

class AdminServer:
    """
    Encapsulates admin server logic: separate port, listening for admin commands, etc.
    """

    def __init__(self, host: str, port: int, main_server):
        """
        :param host: IP or hostname for admin server to bind
        :param port: port for admin server
        :param main_server: reference to the main server instance
        """
        self.host = host
        self.port = port
        self.main_server = main_server
        self.server_socket = None
        self.running = False

    def register(self):
        """
        Start the Admin server in a separate thread. 
        """
        logging.info("[AdminServer] Initializing admin server plugin...")
        self.running = True

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        logging.info(f"[AdminServer] Listening on {self.host}:{self.port}")

        t = threading.Thread(target=self._accept_loop, daemon=True)
        t.start()
        return self.server_socket

    def unregister(self):
        """
        Stop the admin server and close the socket if necessary.
        """
        logging.info("[AdminServer] Shutting down admin server plugin...")
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                logging.error(f"[AdminServer] Error closing socket: {e}")
        return None

    def _accept_loop(self):
        """
        Accept admin connections in a loop. Each connection in a new thread.
        """
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                t = threading.Thread(
                    target=self._admin_session,
                    args=(conn, addr),
                    daemon=True
                )
                t.start()
            except OSError:
                # Socket likely closed
                break
            except Exception as e:
                logging.error(f"[AdminServer] Error in accept loop: {e}")
                break

    def _admin_session(self, conn, addr):
        """
        Interactive admin session: reads commands and returns output.
        """
        logging.info(f"[AdminServer] Admin connection from {addr}")
        with conn:
            try:
                conn.sendall(b"Welcome to Admin console. Type 'help' for commands.\n> ")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    cmd_line = data.decode().strip()
                    if cmd_line.lower() in ("exit", "quit"):
                        conn.sendall(b"Bye.\n")
                        break
                    response = self._handle_admin_command(cmd_line)
                    conn.sendall(response.encode('utf-8') + b"\n> ")
            except Exception as e:
                logging.error(f"[AdminServer] Error in admin session: {e}")

    def _handle_admin_command(self, cmd_line: str) -> str:
        """
        Parse and respond to admin commands.
        """
        if not cmd_line:
            return ""

        parts = cmd_line.split()
        cmd = parts[0].lower()

        # ------------------
        # Built-in commands
        # ------------------
        if cmd in ("help", "?"):
            return (
                "Admin Commands:\n"
                "  help / ?                - Show this help\n"
                "  status                  - Show server status\n"
                "  list                    - List discovered plugins + status\n"
                "  list connections        - List active client connections\n"
                "  enable <plugin>         - Enable a discovered plugin\n"
                "  disable <plugin>        - Disable an enabled plugin\n"
                "  change pass <new_pass>  - Change server password\n"
                "  regen_SSL_certs         - Regenerate local SSL certificates, reload TLS plugin\n"
                "  exit / quit             - Close this admin session\n"
            )
        elif cmd == "status":
            return self.main_server.get_status()

        elif cmd == "list":
            # Could check if second argument is 'connections'
            if len(parts) == 2 and parts[1].lower() == "connections":
                return self._list_connections()
            else:
                return self.main_server.list_plugins()

        elif cmd == "enable" and len(parts) == 2:
            plugin_name = parts[1]
            self.main_server.enable_plugin(plugin_name)
            return f"Plugin '{plugin_name}' enabled."

        elif cmd == "disable" and len(parts) == 2:
            plugin_name = parts[1]
            self.main_server.disable_plugin(plugin_name)
            return f"Plugin '{plugin_name}' disabled."

        elif cmd == "change" and len(parts) >= 3 and parts[1].lower() == "pass":
            old_pass = self.main_server.SERVER_PASSWORD
            new_pass = parts[2]
            self.main_server.SERVER_PASSWORD = new_pass
            return f"Password changed from '{old_pass}' to '{new_pass}'"

        elif cmd == "regen_ssl_certs":
            return self._regen_ssl_certs()

        else:
            return f"Unknown command '{cmd_line}'. Type 'help' for usage."

    def _list_connections(self) -> str:
        """
        Retrieve a list of currently active connections from client_management plugin (if enabled).
        """
        cm = self.main_server.ENABLED_PLUGINS.get("client_management", None)
        if cm and hasattr(cm, "list_connections"):
            return cm.list_connections()
        return "client_management plugin is not enabled or doesn't support listing connections."

    def _regen_ssl_certs(self) -> str:
        """
        Regenerate local certificates and reload the TLS plugin.
        """
        tls_plugin = self.main_server.ENABLED_PLUGINS.get("tls_support", None)
        if not tls_plugin:
            return "TLS plugin is not enabled. Enable 'tls_support' first."
        if not hasattr(tls_plugin, "regenerate_certs"):
            return "TLS plugin does not support certificate regeneration."
        try:
            tls_plugin.regenerate_certs()
            # Optional: re-register plugin to reload the SSL context
            if hasattr(tls_plugin, "register"):
                self.main_server.MAIN_SERVER_SOCKET = tls_plugin.register(
                    self.main_server.MAIN_SERVER_SOCKET
                )
            return "SSL certificates regenerated and TLS plugin reloaded."
        except Exception as e:
            return f"Error regenerating certs: {e}"