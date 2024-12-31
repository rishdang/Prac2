import logging


class KeyloggingPlugin:
    """
    A plugin to manage keylogging functionality for clients.
    This can be enabled or disabled dynamically through the operator shell.
    """

    def __init__(self, client_management):
        self.client_management = client_management
        self.enabled = False  # Keylogging is disabled by default

    def enable(self):
        """Enable keylogging for the active client."""
        if self.enabled:
            return "Keylogging is already enabled."
        self.enabled = True
        response = self.client_management.start_keylogging()
        logging.info("[KeyloggingPlugin] Keylogging enabled.")
        return response or "Keylogging enabled successfully."

    def disable(self):
        """Disable keylogging for the active client."""
        if not self.enabled:
            return "Keylogging is already disabled."
        self.enabled = False
        response = self.client_management.stop_keylogging()
        logging.info("[KeyloggingPlugin] Keylogging disabled.")
        return response or "Keylogging disabled successfully."

    def status(self):
        """Check the status of keylogging."""
        status = "enabled" if self.enabled else "disabled"
        return f"Keylogging is currently {status}."

    def handle_command(self, command):
        """Handle commands related to the keylogging plugin."""
        if command == "enable":
            return self.enable()
        elif command == "disable":
            return self.disable()
        elif command == "status":
            return self.status()
        else:
            return "Unknown command. Available commands: enable, disable, status."