import logging

class CommandHandler:
    """
    Handles the parsing and execution of commands.
    """

    def __init__(self, main_server):
        """
        Initializes the CommandHandler.

        Args:
            main_server: The main server instance.
        """
        self.main_server = main_server
        self.commands = {
            "help": self.get_help,
            "status": self.show_status,
            "enable": self.enable_plugin,
            "disable": self.disable_plugin,
            "list": self.list_active_clients,
            "exit": self.exit_shell,
        }

    def handle_command(self, command):
        """
        Parses and executes a command.

        Args:
            command (str): The command string.

        Returns:
            str: The result of the command.
        """
        parts = command.strip().split()
        if not parts:
            return "Invalid command."

        cmd = parts[0].lower()
        if cmd in self.commands:
            return self.commands[cmd](parts[1:])  # Pass arguments to the handler
        else:
            return f"Unknown command: {cmd}"

    def get_help(self, args=None):
        """
        Returns the help message.

        Args:
            args (list): Command arguments (unused).

        Returns:
            str: Help message.
        """
        return (
            "Available Commands:\n"
            "  help               - Show this help message.\n"
            "  status             - Show server status.\n"
            "  enable <plugin>    - Enable a plugin.\n"
            "  disable <plugin>   - Disable a plugin.\n"
            "  list               - List active client connections.\n"
            "  exit               - Exit the shell or client session.\n"
        )

    def show_status(self, args=None):
        """
        Displays the server's current status.

        Args:
            args (list): Command arguments (unused).

        Returns:
            str: Status message.
        """
        return self.main_server.show_status()

    def enable_plugin(self, args):
        """
        Enables a plugin.

        Args:
            args (list): Command arguments.

        Returns:
            str: Result message.
        """
        if not args:
            return "Usage: enable <plugin>"
        plugin = args[0]
        if self.main_server.enable_plugin(plugin):
            return f"Plugin '{plugin}' enabled."
        return f"Failed to enable plugin '{plugin}'."

    def disable_plugin(self, args):
        """
        Disables a plugin.

        Args:
            args (list): Command arguments.

        Returns:
            str: Result message.
        """
        if not args:
            return "Usage: disable <plugin>"
        plugin = args[0]
        if self.main_server.disable_plugin(plugin):
            return f"Plugin '{plugin}' disabled."
        return f"Failed to disable plugin '{plugin}'."

    def list_active_clients(self, args=None):
        """
        Lists all active client connections.

        Args:
            args (list): Command arguments (unused).

        Returns:
            str: List of active clients.
        """
        active_clients = self.main_server.client_management.list_active_clients()
        if not active_clients:
            return "No active clients."
        return f"Active Clients: {', '.join(map(str, active_clients))}"

    def exit_shell(self, args=None):
        """
        Exits the shell or client session.

        Args:
            args (list): Command arguments (unused).

        Returns:
            str: Exit message.
        """
        self.main_server.operator_session.running_shell = False
        return "Exiting shell."