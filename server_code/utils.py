import logging

def configure_logging(log_file="server.log"):
    """
    Configures logging for the server.

    Args:
        log_file: Path to the log file. Default is 'server.log'.
    """
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger().addHandler(logging.StreamHandler())

def authenticate_client(conn, expected_password, buffer_size=1024):
    """
    Authenticates a client by receiving and validating a password.

    Args:
        conn: Client connection socket.
        expected_password: The password to authenticate against.
        buffer_size: Buffer size for receiving data.

    Returns:
        bool: True if authenticated, False otherwise.
    """
    try:
        conn.send(b"Enter password: ")
        password = conn.recv(buffer_size).decode(errors="replace").strip()
        if password == expected_password:
            conn.send(b"REMOTE_SHELL_CONFIRMED\n")
            logging.info("[Utils] Client authenticated successfully.")
            return True
        else:
            conn.send(b"AUTHENTICATION_FAILED\n")
            logging.warning("[Utils] Client authentication failed.")
            return False
    except Exception as e:
        logging.error(f"[Utils] Error during authentication: {e}")
        return False

def get_operator_banner():
    """
    Returns the operator shell banner.

    Returns:
        str: Banner string to display.
    """
    return (
        "----------------------------------------\n"
        " Welcome to PRAC2 C2 Server Shell\n"
        "----------------------------------------\n"
    )

def manage_plugin(plugin_name, action, available_plugins, enabled_plugins):
    """
    Enables or disables a plugin.

    Args:
        plugin_name: The name of the plugin.
        action: "enable" or "disable".
        available_plugins: Dictionary of available plugins.
        enabled_plugins: Dictionary of enabled plugins.

    Returns:
        str: Status message indicating the result of the operation.
    """
    if action == "enable":
        if plugin_name in available_plugins:
            enabled_plugins[plugin_name] = available_plugins[plugin_name]
            logging.info(f"[Utils] Plugin '{plugin_name}' enabled.")
            return f"Plugin '{plugin_name}' enabled."
        logging.warning(f"[Utils] Plugin '{plugin_name}' not found.")
        return f"Plugin '{plugin_name}' not found."
    elif action == "disable":
        if plugin_name in enabled_plugins:
            del enabled_plugins[plugin_name]
            logging.info(f"[Utils] Plugin '{plugin_name}' disabled.")
            return f"Plugin '{plugin_name}' disabled."
        logging.warning(f"[Utils] Plugin '{plugin_name}' is not enabled.")
        return f"Plugin '{plugin_name}' is not enabled."
    else:
        logging.error("[Utils] Invalid plugin management action.")
        return "Invalid action. Use 'enable' or 'disable'."