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

# import banner
from server_code.banner import show_startup_banner

class MainServer:
    """
    Main server class that:
      - Discovers/loads plugins from 'capabilities/'
      - Maintains references to discovered (DISCOVERED_PLUGINS) and enabled (ENABLED_PLUGINS) plugins
      - Accepts client connections on MAIN_PORT (auto-increment if in use)
      - Runs the Admin Server on ADMIN_PORT (also auto-increment)
      - Coordinates with:
          * client_management (operator shell, not a plugin)
          * client_commands (authentication + server console commands)
      - Preserves banner logic and multi_client_support.
    """

    def __init__(self):
        self.HOST = '127.0.0.1'
        self.MAIN_PORT = DEFAULT_MAIN_PORT
        self.ADMIN_PORT = DEFAULT_ADMIN_PORT

        self.SERVER_PASSWORD = "mysecretpass1"  # Must be exactly 12 chars
        self.BUFFER_SIZE = 512

        # Track discovered & enabled plugin modules
        self.DISCOVERED_PLUGINS = {}
        self.ENABLED_PLUGINS = {}

        # References to server sockets / modules
        self.MAIN_SERVER_SOCKET = None
        self.admin_server_plugin = None

        # We'll attach references to server_code modules here
        self.client_commands = None
        self.client_management = None  # Not a plugin, just a core module

    # -----------------------------------------------------------
    #         CAPABILITIES LOADING & PLUGIN MANAGEMENT
    # -----------------------------------------------------------
    def load_capabilities(self, capabilities_dir: str = "capabilities"):
        """
        Dynamically discover .py files in 'capabilities/' as plugin modules.
        """
        if not os.path.isdir(capabilities_dir):
            logging.warning(f"Capabilities directory '{capabilities_dir}' not found.")
            return

        for filename in os.listdir(capabilities_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
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
        Returns a string listing discovered plugins, showing which are enabled/disabled.
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
        Returns a string describing server state: password, main/admin ports, enabled plugins.
        Also # of connected clients & operator shell info if client_management is present.
        """
        lines = []
        lines.append(f"Server password: {self.SERVER_PASSWORD}")
        lines.append(f"Main port: {self.MAIN_PORT}, Admin port: {self.ADMIN_PORT}")

        if self.ENABLED_PLUGINS:
            lines.append("Enabled plugins: " + ", ".join(self.ENABLED_PLUGINS.keys()))
        else:
            lines.append("No plugins enabled.")

        if self.client_management:
            client_count = self.client_management.get_client_count()
            lines.append(f"Number of connected clients: {client_count}")

            shell_info = self.client_management.get_operator_shell_info()
            lines.append(shell_info)
        else:
            lines.append("client_management is not set up.")

        return "\n".join(lines)

    # -----------------------------------------------------------
    #                   MAIN SERVER LOOP
    # -----------------------------------------------------------
    def run_main_server(self):
        """
        Accept client connections on MAIN_PORT. If that port is in use,
        we auto-increment the port number until we find a free one.
        """

        # Attempt to bind until successful
        while True:
            try:
                self.MAIN_SERVER_SOCKET.bind((self.HOST, self.MAIN_PORT))
                break
            except OSError as e:
                # Typically, e.errno == 98 means 'Address already in use' on Unix-like systems
                if hasattr(e, 'errno') and e.errno == 98:
                    logging.warning(f"[MainServer] Port {self.MAIN_PORT} in use. Trying next port...")
                    self.MAIN_PORT += 1
                else:
                    raise e

        self.MAIN_SERVER_SOCKET.listen()
        logging.info(f"[MainServer] Listening on {self.HOST}:{self.MAIN_PORT}")

        # Check if multi_client_support is enabled
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

    # Prompt user for main/admin ports (optional)
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

    # 1) Load capabilities from 'capabilities/' (plugins)
    server.load_capabilities("capabilities")

    # 2) Create main server socket
    server.MAIN_SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 3) Admin server plugin
    from server_code.admin_server import AdminServer
    server.admin_server_plugin = AdminServer(server.HOST, server.ADMIN_PORT, server)
    server.admin_server_plugin.register()

    # 4) Client management (operator shell). Not a plugin in ENABLED_PLUGINS
    from server_code.client_management import ClientManagement
    server.client_management = ClientManagement(server)
    server.client_management.register(server.MAIN_SERVER_SOCKET)

    # 5) Client commands
    from server_code.client_commands import ClientCommands
    server.client_commands = ClientCommands(server)
    server.MAIN_SERVER_SOCKET = server.client_commands.register(server.MAIN_SERVER_SOCKET)

    # 6) Run the main server
    server.run_main_server()

    logging.info("=== Prac2 Server has stopped. ===")

if __name__ == "__main__":
    main()