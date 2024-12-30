#!/usr/bin/env python3

import socket
import logging
import sys
import os
import importlib
import threading

# -------------- Defaults --------------
DEFAULT_MAIN_PORT = 27015
DEFAULT_ADMIN_PORT = 9999

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# We import our startup banner from server_code/banner
from server_code.banner import show_startup_banner

class MainServer:
    """
    Main server class that:
      - Discovers/loads plugins from 'capabilities/'
      - Holds references to discovered and enabled plugins
      - Accepts client connections on MAIN_PORT
      - Runs the Admin Server on ADMIN_PORT
      - Provides list_plugins() and get_status() for admin usage
      - Coordinates with client_management (operator shell) and client_commands
    """

    def __init__(self):
        self.HOST = '127.0.0.1'
        self.MAIN_PORT = DEFAULT_MAIN_PORT
        self.ADMIN_PORT = DEFAULT_ADMIN_PORT

        self.SERVER_PASSWORD = "mysecretpass1"  # Must be exactly 12 chars
        self.BUFFER_SIZE = 512

        # Keep track of discovered & enabled plugins
        self.DISCOVERED_PLUGINS = {}
        self.ENABLED_PLUGINS = {}

        # References
        self.MAIN_SERVER_SOCKET = None
        self.admin_server_plugin = None

        # We'll attach references to server_code modules here
        self.client_commands = None
        self.client_management = None

    # -----------------------------------------------------------
    #         CAPABILITIES LOADING & PLUGIN MANAGEMENT
    # -----------------------------------------------------------
    def load_capabilities(self, capabilities_dir: str = "capabilities"):
        """
        Dynamically discover .py files in 'capabilities/' as plugins.
        """
        if not os.path.isdir(capabilities_dir):
            logging.warning(f"Capabilities directory '{capabilities_dir}' not found.")
            return

        for filename in os.listdir(capabilities_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]  # remove '.py'
                module_path = f"{capabilities_dir}.{module_name}"
                try:
                    module = importlib.import_module(module_path)
                    self.DISCOVERED_PLUGINS[module_name] = module
                    logging.info(f"Discovered capability: {module_name}")
                except Exception as e:
                    logging.error(f"Error loading capability '{module_name}': {e}")

    def enable_plugin(self, plugin_name):
        """
        Enable a plugin by calling its register() if defined.
        """
        if plugin_name in self.ENABLED_PLUGINS:
            logging.info(f"Plugin '{plugin_name}' is already enabled.")
            return

        if plugin_name not in self.DISCOVERED_PLUGINS:
            logging.warning(f"No such plugin '{plugin_name}' was discovered.")
            return

        plugin_module = self.DISCOVERED_PLUGINS[plugin_name]
        logging.info(f"Enabling plugin '{plugin_name}'...")

        if hasattr(plugin_module, "register"):
            try:
                new_socket = plugin_module.register(self.MAIN_SERVER_SOCKET)
                # If plugin returns a wrapped socket (TLS, etc.), store it
                if new_socket:
                    self.MAIN_SERVER_SOCKET = new_socket
            except Exception as e:
                logging.error(f"Error registering plugin '{plugin_name}': {e}")
                return

        self.ENABLED_PLUGINS[plugin_name] = plugin_module
        logging.info(f"Plugin '{plugin_name}' has been ENABLED.")

    def disable_plugin(self, plugin_name):
        """
        Disable a plugin by calling its unregister() if defined.
        """
        if plugin_name not in self.ENABLED_PLUGINS:
            logging.info(f"Plugin '{plugin_name}' is not currently enabled.")
            return

        plugin_module = self.ENABLED_PLUGINS[plugin_name]
        logging.info(f"Disabling plugin '{plugin_name}'...")

        if hasattr(plugin_module, "unregister"):
            try:
                new_socket = plugin_module.unregister(self.MAIN_SERVER_SOCKET)
                if new_socket:
                    self.MAIN_SERVER_SOCKET = new_socket
            except Exception as e:
                logging.error(f"Error unregistering plugin '{plugin_name}': {e}")

        del self.ENABLED_PLUGINS[plugin_name]
        logging.info(f"Plugin '{plugin_name}' has been DISABLED.")

    def list_plugins(self) -> str:
        """
        Return a string listing discovered plugins and whether each is enabled/disabled.
        """
        lines = ["Discovered plugins:"]
        for p in self.DISCOVERED_PLUGINS:
            status = "ENABLED" if p in self.ENABLED_PLUGINS else "DISABLED"
            lines.append(f"  {p} ({status})")
        return "\n".join(lines)

    # -----------------------------------------------------------
    #                      STATUS REPORT
    # -----------------------------------------------------------
    def get_status(self) -> str:
        """
        Return a string describing server state (password, ports, enabled plugins, etc.).
        Also show # of clients and operator shell info if client_management is enabled.
        """
        lines = []
        lines.append(f"Server password: {self.SERVER_PASSWORD}")
        lines.append(f"Main port: {self.MAIN_PORT}, Admin port: {self.ADMIN_PORT}")

        if self.ENABLED_PLUGINS:
            lines.append("Enabled plugins: " + ", ".join(self.ENABLED_PLUGINS.keys()))
        else:
            lines.append("No plugins enabled.")

        cm_plugin = self.ENABLED_PLUGINS.get("client_management", None)
        if cm_plugin:
            client_count = cm_plugin.get_client_count()
            lines.append(f"Number of connected clients: {client_count}")
            shell_info = cm_plugin.get_operator_shell_info()
            lines.append(shell_info)
        else:
            lines.append("ClientManagement plugin is not enabled.")

        return "\n".join(lines)

    # -----------------------------------------------------------
    #                   MAIN SERVER LOOP
    # -----------------------------------------------------------
    def run_main_server(self):
        """
        Accept client connections on MAIN_PORT. 
        If multi_client_support is enabled, handle concurrency in threads,
        else handle single connection at a time.
        """
        self.MAIN_SERVER_SOCKET.bind((self.HOST, self.MAIN_PORT))
        self.MAIN_SERVER_SOCKET.listen()

        logging.info(f"[MainServer] Listening on {self.HOST}:{self.MAIN_PORT}")

        is_multi = ("multi_client_support" in self.ENABLED_PLUGINS)
        if is_multi:
            logging.info("[MainServer] Multi-client mode is ENABLED.")
        else:
            logging.info("[MainServer] Multi-client mode is DISABLED (one client at a time).")

        while True:
            try:
                conn, addr = self.MAIN_SERVER_SOCKET.accept()

                # Let client_management track it
                if self.client_management and hasattr(self.client_management, "on_connection_accepted"):
                    self.client_management.on_connection_accepted(conn, addr)

                if is_multi:
                    # concurrency
                    t = threading.Thread(
                        target=self.client_commands.handle_client,
                        args=(conn, addr),
                        daemon=True
                    )
                    t.start()
                else:
                    # single client only
                    self.client_commands.handle_client(conn, addr)

            except KeyboardInterrupt:
                logging.info("[MainServer] Interrupted. Shutting down.")
                break
            except Exception as e:
                logging.error(f"[MainServer] Error in main loop: {e}")
                break

        try:
            self.MAIN_SERVER_SOCKET.close()
        except:
            pass


def main():
    # Show the startup banner in the console
    show_startup_banner()

    logging.info("=== Starting Prac2 Server ===")

    server = MainServer()

    # Prompt user for main/admin ports if desired
    try:
        mp = input(f"Enter main server port (default {DEFAULT_MAIN_PORT}): ").strip()
        if mp:
            server.MAIN_PORT = int(mp)
    except:
        logging.warning("Invalid main port input; using default.")

    try:
        ap = input(f"Enter admin server port (default {DEFAULT_ADMIN_PORT}): ").strip()
        if ap:
            server.ADMIN_PORT = int(ap)
    except:
        logging.warning("Invalid admin port input; using default.")

    # 1) Load capabilities
    server.load_capabilities("capabilities")

    # 2) Create main server socket
    server.MAIN_SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 3) Admin server plugin
    from server_code.admin_server import AdminServer
    server.admin_server_plugin = AdminServer(server.HOST, server.ADMIN_PORT, server)
    server.admin_server_plugin.register()

    # 4) Client management (operator shell)
    from server_code.client_management import ClientManagement
    server.client_management = ClientManagement(server)
    server.client_management.register(server.MAIN_SERVER_SOCKET)

    # 5) Client commands
    from server_code.client_commands import ClientCommands
    server.client_commands = ClientCommands(server)
    server.MAIN_SERVER_SOCKET = server.client_commands.register(server.MAIN_SERVER_SOCKET)

    # 6) Run main server
    server.run_main_server()

    logging.info("=== Prac2 Server has stopped. ===")


if __name__ == "__main__":
    main()