import logging
from command_handler import CommandHandler
from utils import get_operator_banner

class OperatorSession:
    """
    Manages the operator shell session.
    """

    def __init__(self, main_server):
        """
        Initializes the OperatorSession.

        Args:
            main_server: The main server instance.
        """
        self.main_server = main_server
        self.running_shell = False
        self.command_handler = CommandHandler(main_server)

    def launch_operator_shell(self):
        """
        Launches the operator shell.
        """
        if self.running_shell:
            logging.info("[OperatorSession] Operator shell is already running.")
            return

        self.running_shell = True
        print(get_operator_banner())
        print("Operator Shell Ready. Type 'help' for commands.\n")

        while self.running_shell:
            try:
                command = input("operator> ").strip()
                if not command:
                    continue

                response = self.command_handler.handle_command(command)
                if response:
                    print(response)
            except (EOFError, KeyboardInterrupt):
                logging.info("[OperatorSession] Operator shell interrupted.")
                break
            except Exception as e:
                logging.error(f"[OperatorSession] Error in shell: {e}")

        logging.info("[OperatorSession] Operator shell closed.")
        self.running_shell = False