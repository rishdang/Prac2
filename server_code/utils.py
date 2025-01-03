import logging
import os
import random
import string

# Global Constants
BUFFER_SIZE = 4096
SERVER_PASSWORD = "mysecretpass1"  # Default password (should be configurable)


def setup_logging(log_file="server.log"):
    """
    Sets up logging for the server.

    Args:
        log_file (str): The file where logs will be written.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def get_operator_banner():
    """
    Generates a banner for the operator shell.

    Returns:
        str: The operator shell banner.
    """
    return (
        "=====================================\n"
        "          PRAC2 Operator Shell       \n"
        "=====================================\n"
        "Type 'help' for a list of commands.\n"
    )


def get_server_status(server):
    """
    Returns the current status of the server.

    Args:
        server: The main server instance.

    Returns:
        str: Server status string.
    """
    status = (
        f"Server running on {server.HOST}:{server.PORT}\n"
        f"Active clients: {len(server.client_manager.get_active_clients())}\n"
        f"Enabled plugins: {', '.join(server.ENABLED_PLUGINS.keys()) or 'None'}"
    )
    return status


def get_enabled_plugins(server):
    """
    Returns a list of enabled plugins.

    Args:
        server: The main server instance.

    Returns:
        list: List of enabled plugin names.
    """
    return list(server.ENABLED_PLUGINS.keys())


def generate_client_id(address):
    """
    Generates a unique ID for a client based on its address.

    Args:
        address (tuple): The client's address (IP, port).

    Returns:
        str: Unique client ID.
    """
    return f"{address[0]}:{address[1]}"


def random_string(length=8):
    """
    Generates a random alphanumeric string.

    Args:
        length (int): Length of the random string.

    Returns:
        str: Random string.
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def clean_temp_files():
    """
    Cleans up temporary files or artifacts left during execution.
    """
    temp_dir = "/tmp/prac2"
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            try:
                os.unlink(file_path)
                logging.info(f"Deleted temp file: {file_path}")
            except Exception as e:
                logging.error(f"Failed to delete {file_path}: {e}")