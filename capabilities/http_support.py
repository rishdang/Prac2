# capabilities/http_support.py

import logging
import socket

def register(server_socket):
    """
    Called when the plugin is enabled (either at server startup or at runtime).
    For an HTTP-based plugin, you might do nothing special or set up an HTTP server library.
    """
    logging.info("[HTTP] HTTP support plugin registered.")
    return server_socket

def on_connection_accepted(conn, addr):
    """
    Called when a new connection is accepted. We could:
      - Immediately send an HTTP welcome banner.
      - Or do a quick 'handshake' to see if the client speaks HTTP.
    """
    logging.info(f"[HTTP] Connection accepted from {addr}, HTTP plugin active.")
    # (Optional) Send a simple banner, purely for demo:
    try:
        conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHello from HTTP plugin!\r\n")
    except Exception as e:
        logging.error(f"[HTTP] Error sending HTTP banner: {e}")

def on_command(command, conn, server_socket):
    """
    If we want to intercept a command, e.g. 'http <something>', do it here.
    Return True if handled, else False.
    """
    parts = command.strip().split()
    if not parts:
        return False

    if parts[0].lower() == "http":
        # e.g. "http send hello"
        if len(parts) > 1 and parts[1].lower() == "send":
            message = " ".join(parts[2:]) or "Hello over HTTP!"
            http_msg = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n\r\n"
                f"{message}\r\n"
            ).encode('utf-8')
            try:
                conn.sendall(http_msg)
                logging.info(f"[HTTP] Sent custom HTTP message: {message}")
            except Exception as e:
                logging.error(f"[HTTP] Failed to send HTTP message: {e}")
        else:
            logging.info("[HTTP] Usage: http send <message>")
        return True

    return False