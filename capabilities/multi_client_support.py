import logging

MULTI_CLIENT_ENABLED = False

def register(server_socket):
    """
    Called when plugin is enabled: set a global or shared variable 
    to indicate multi-client concurrency.
    """
    logging.info("[MultiClient] Multi-client support ENABLED.")
    global MULTI_CLIENT_ENABLED
    MULTI_CLIENT_ENABLED = True
    return server_socket

def unregister(server_socket):
    """
    Called when plugin is disabled: revert multi-client mode.
    """
    logging.info("[MultiClient] Multi-client support DISABLED.")
    global MULTI_CLIENT_ENABLED
    MULTI_CLIENT_ENABLED = False
    return server_socket

def on_command(command, conn, server_socket):
    """
    If you want to parse commands like "multiclient status" or so, do it here.
    Return True if handled, else False.
    """
    parts = command.strip().split()
    if len(parts) >= 1 and parts[0].lower() == "multiclient":
        # just a sample usage
        if len(parts) == 2 and parts[1].lower() == "status":
            message = "MULTI_CLIENT_ENABLED = " + str(MULTI_CLIENT_ENABLED)
            try:
                conn.sendall((message + "\n").encode('utf-8'))
            except:
                pass
            return True
        return True
    return False