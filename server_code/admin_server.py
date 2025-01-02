import logging
from utils import manage_plugin, configure_logging

class AdminServer:
    """
    Provides administrative controls for the PRAC2 server.
    """

    def __init__(self, main_server):
        """
        Initializes the AdminServer.

        Args:
            main_server: The main server instance.
        """
        self.main_server = main_server
        configure_logging()

    def enable_plugin(self, plugin_name):
        """
        Enables a plugin dynamically.

        Args:
            plugin_name: The name of the plugin to enable.

        Returns:
            str: Status message indicating the result of the operation.
        """
        return manage_plugin(
            plugin_name, "enable", self.main_server.AVAILABLE_PLUGINS, self.main_server.ENABLED_PLUGINS
        )

    def disable_plugin(self, plugin_name):
        """
        Disables a plugin dynamically.

        Args:
            plugin_name: The name of the plugin to disable.

        Returns:
            str: Status message indicating the result of the operation.
        """
        return manage_plugin(
            plugin_name, "disable", self.main_server.AVAILABLE_PLUGINS, self.main_server.ENABLED_PLUGINS
        )

    def list_plugins(self):
        """
        Lists all available and enabled plugins.

        Returns:
            dict: A dictionary containing available and enabled plugins.
        """
        return {
            "available": list(self.main_server.AVAILABLE_PLUGINS.keys()),
            "enabled": list(self.main_server.ENABLED_PLUGINS.keys()),
        }

    def change_password(self, new_password):
        """
        Changes the server's authentication password.

        Args:
            new_password: The new password to set.
        """
        old_password = self.main_server.SERVER_PASSWORD
        self.main_server.SERVER_PASSWORD = new_password
        logging.info(f"[AdminServer] Password changed from '{old_password}' to '{new_password}'.")

    def show_status(self):
        """
        Displays the current status of the server.

        Returns:
            str: A status message.
        """
        return (
            f"Server running on {self.main_server.HOST}:{self.main_server.PORT}\n"
            f"Active clients: {len(self.main_server.client_management.clients)}\n"
            f"Enabled plugins: {list(self.main_server.ENABLED_PLUGINS.keys())}"
        )