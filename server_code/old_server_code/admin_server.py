# server_code/admin_server.py

import socket
import logging
import threading
from server_code.banner import get_admin_banner

class AdminServer:
    """
    The admin server runs on a separate port, letting an admin connect
    to run commands like 'status', 'list connections', 'enable <plugin>', etc.
    If the desired port (default 9999) is taken, we auto-increment until we find a free one.
    """

    def __init__(self, host: str, port: int, main_server):
        self.host = host
        self.port = port
        self.main_server = main_server
        self.server_socket = None
        self.running = False

    def register(self):
        """
        Start the Admin server in a background thread,
        auto-incrementing 'self.port' if needed.
        """
        logging.info("[AdminServer] Initializing admin server plugin...")
        self.running = True

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        while True:
            try:
                self.server_socket.bind((self.host, self.port))
                break
            except OSError as e:
                # On Unix-likes, errno=98 => 'Address already in use'
                if hasattr(e, 'errno') and e.errno == 98:
                    logging.warning(f"[AdminServer] Port {self.port} in use. Trying next port...")
                    self.port += 1
                else:
                    raise e

        self.server_socket.listen()
        logging.info(f"[AdminServer] Listening on {self.host}:{self.port}")

        t = threading.Thread(target=self._accept_loop, daemon=True)
        t.start()
        return self.server_socket

    def unregister(self):
        logging.info("[AdminServer] Shutting down admin server plugin...")
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                logging.error(f"[AdminServer] Error closing socket: {e}")
        return None

    def _accept_loop(self):
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
                break
            except Exception as e:
                logging.error(f"[AdminServer] Error in accept loop: {e}")
                break

    def _admin_session(self, conn, addr):
        logging.info(f"[AdminServer] Admin connection from {addr}")
        with conn:
            try:
                # Display the ASCII banner for admin
                banner = get_admin_banner()
                conn.sendall(banner.encode('utf-8'))
                conn.sendall(b"\nType 'help' for commands.\n> ")

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
        Uses self.main_server for status, plugin mgmt, etc.
        Directly calls self.main_server.client_management for 'list connections'.
        """
        if not cmd_line:
            return ""

        parts = cmd_line.split()
        cmd = parts[0].lower()

        if cmd in ("help", "?"):
            return (
                "Admin Commands:\n"
                "  help / ?                - Show this help\n"
                "  status                  - Show server status\n"
                "  list                    - List discovered plugins + status\n"
                "  list connections        - Show connected clients (via client_management)\n"
                "  enable <plugin>         - Enable a discovered plugin\n"
                "  disable <plugin>        - Disable an enabled plugin\n"
                "  change pass <new_pass>  - Change server password\n"
                "  regen_ssl_certs         - Regenerate TLS certs and reload plugin\n"
                "  exit / quit             - Close this admin session"
            )

        elif cmd == "status":
            return self.main_server.get_status()

        elif cmd == "list":
            if len(parts) == 2 and parts[1].lower() == "connections":
                # Directly call the client_management object
                cm = self.main_server.client_management
                if cm and hasattr(cm, "list_connections"):
                    return cm.list_connections()
                else:
                    return "client_management is not available or no list_connections method."
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

    def _regen_ssl_certs(self) -> str:
        """
        If TLS plugin is enabled, call regenerate_certs() then re-register.
        """
        tls_plugin = self.main_server.ENABLED_PLUGINS.get("tls_support", None)
        if not tls_plugin:
            return "TLS plugin not enabled. Enable 'tls_support' first."
        if not hasattr(tls_plugin, "regenerate_certs"):
            return "TLS plugin does not support certificate regeneration."
        try:
            tls_plugin.regenerate_certs()
            if hasattr(tls_plugin, "register"):
                self.main_server.MAIN_SERVER_SOCKET = tls_plugin.register(
                    self.main_server.MAIN_SERVER_SOCKET
                )
            return "SSL certs regenerated, TLS plugin reloaded."
        except Exception as e:
            return f"Error regenerating certs: {e}"