import logging
from server_code.utils import get_server_status, get_enabled_plugins


class AdminServer:
    """
    Handles server administration tasks such as managing plugins, 
    showing status, and logging errors.
    """

    def __init__(self, main_server):
        self.main_server = main_server

    def enable_plugin(self, plugin_name):
        """
        Enables a plugin by name.
        """
        if self.main_server.enable_plugin(plugin_name):
            logging.info(f"[AdminServer] Plugin '{plugin_name}' enabled successfully.")
            return f"Plugin '{plugin_name}' enabled."
        else:
            logging.warning(f"[AdminServer] Failed to enable plugin '{plugin_name}'.")
            return f"Failed to enable plugin '{plugin_name}'."

    def disable_plugin(self, plugin_name):
        """
        Disables a plugin by name.
        """
        if self.main_server.disable_plugin(plugin_name):
            logging.info(f"[AdminServer] Plugin '{plugin_name}' disabled successfully.")
            return f"Plugin '{plugin_name}' disabled."
        else:
            logging.warning(f"[AdminServer] Failed to disable plugin '{plugin_name}'.")
            return f"Failed to disable plugin '{plugin_name}'."

    def list_plugins(self):
        """
        Lists all enabled plugins.
        """
        plugins = get_enabled_plugins(self.main_server)
        if not plugins:
            return "No plugins are currently enabled."
        return f"Enabled Plugins:\n" + "\n".join([f"- {plugin}" for plugin in plugins])

    def show_status(self):
        """
        Displays the server status, including active connections and plugins.
        """
        status = get_server_status(self.main_server)
        logging.info("[AdminServer] Showing server status.")
        return status

    def change_password(self, new_password):
        """
        Changes the server password.
        """
        old_password = self.main_server.SERVER_PASSWORD
        self.main_server.SERVER_PASSWORD = new_password
        logging.info(f"[AdminServer] Password changed successfully.")
        return f"Password changed from '{old_password}' to '{new_password}'."

    def handle_admin_command(self, command):
        """
        Processes administrative commands.
        """
        parts = command.split()
        cmd_name = parts[0].lower()

        if cmd_name == "status":
            return self.show_status()
        elif cmd_name == "enable" and len(parts) == 2:
            return self.enable_plugin(parts[1])
        elif cmd_name == "disable" and len(parts) == 2:
            return self.disable_plugin(parts[1])
        elif cmd_name == "list" and len(parts) == 2 and parts[1] == "plugins":
            return self.list_plugins()
        elif cmd_name == "change" and len(parts) == 3 and parts[1] == "pass":
            return self.change_password(parts[2])
        else:
            logging.warning(f"[AdminServer] Unknown admin command: {command}")
            return f"Unknown admin command: {command}. Type 'help' for assistance."