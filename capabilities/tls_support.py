import logging
import ssl
import os
import subprocess

CERT_FILE = "local_server.crt"
KEY_FILE = "local_server.key"

def register(server_socket):
    """
    Called every time TLS plugin is enabled.
    Regenerate SSL certs, then wrap the server socket.
    """
    logging.info("[TLS] Enabling TLS support.")
    regenerate_certs()

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

    tls_socket = context.wrap_socket(server_socket, server_side=True)
    logging.info("[TLS] TLS socket is now enabled.")
    return tls_socket

def unregister(server_socket):
    """
    If you want to revert or remove certs upon disable.
    """
    logging.info("[TLS] Disabling TLS support. Removing certs for demonstration.")
    try:
        if os.path.exists(CERT_FILE):
            os.remove(CERT_FILE)
        if os.path.exists(KEY_FILE):
            os.remove(KEY_FILE)
        logging.info("[TLS] Certs removed.")
    except Exception as e:
        logging.error(f"[TLS] Error removing certs: {e}")
    return server_socket

def on_command(command, conn, server_socket):
    """
    If we want to allow 'tls renew' or 'tls info' from server console, etc.
    """
    parts = command.strip().split()
    if len(parts) >= 1 and parts[0].lower() == "tls":
        # example
        return True
    return False

def regenerate_certs():
    """
    Example self-signed cert generation using openssl.
    """
    logging.info("[TLS] Regenerating certs.")
    try:
        if os.path.exists(CERT_FILE):
            os.remove(CERT_FILE)
        if os.path.exists(KEY_FILE):
            os.remove(KEY_FILE)
    except:
        pass

    cmd = [
        "openssl", "req",
        "-new", "-x509",
        "-days", "365",
        "-nodes",
        "-out", CERT_FILE,
        "-keyout", KEY_FILE,
        "-subj", "/CN=localhost"
    ]
    try:
        subprocess.check_call(cmd)
        logging.info("[TLS] Self-signed certificate created via OpenSSL.")
    except FileNotFoundError:
        logging.error("[TLS] OpenSSL not found. Install or use another method.")
    except subprocess.CalledProcessError as e:
        logging.error(f"[TLS] Error generating cert with OpenSSL: {e}")