import socket
import logging

def register(server_socket):
    """
    Called when the plugin is enabled to allow initialization.
    For port scanning, we just log that the plugin is ready.
    """
    logging.info("[PortScanner] Plugin loaded.")
    return server_socket

def on_command(command, conn, server_socket):
    """
    Intercept and handle a 'portscan' command from the server console.
    Example usage:
      portscan <target_host> <port_range>

    - <target_host>: A hostname or IP (e.g., 'google.com', '192.168.1.1')
    - <port_range>:  A single port (e.g. 80) or a range 'start-end' (e.g. '80-85')

    Returns:
      True  if this plugin handled the command
      False otherwise (so other plugins/logic can process it).
    """
    parts = command.strip().split()
    if parts[0].lower() != "portscan":
        return False  # Not our command; let other plugins handle
    
    if len(parts) < 2:
        logging.info("[PortScanner] Usage: portscan <host> [port-or-range]")
        return True

    # Parse arguments
    host = parts[1]
    if len(parts) == 2:
        # No port specified, default to 80
        start_port, end_port = 80, 80
    else:
        # parse the port or port range
        range_str = parts[2]
        if '-' in range_str:
            try:
                start_port, end_port = map(int, range_str.split('-', 1))
            except ValueError:
                logging.warning("[PortScanner] Invalid port range specified.")
                return True
            if start_port > end_port:
                logging.warning("[PortScanner] Start port is greater than end port.")
                return True
        else:
            # Single port
            try:
                start_port = end_port = int(range_str)
            except ValueError:
                logging.warning("[PortScanner] Invalid port specified.")
                return True

    logging.info(f"[PortScanner] Scanning {host} on ports {start_port}-{end_port}...")

    open_ports = []
    timeout = 0.5  # seconds
    for port in range(start_port, end_port + 1):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            result = s.connect_ex((host, port))
            s.close()
            if result == 0:
                open_ports.append(port)
        except Exception as e:
            # e.g. DNS failure, or other error
            logging.warning(f"[PortScanner] Error scanning {host}:{port} => {e}")
    
    if open_ports:
        open_str = ", ".join(map(str, open_ports))
        logging.info(f"[PortScanner] Open ports for {host}: {open_str}")
        # Optionally, send summary back to client
        try:
            conn.sendall(f"Open ports on {host}: {open_str}\n".encode('utf-8'))
        except:
            pass
    else:
        logging.info(f"[PortScanner] No open ports found for {host}.")
        try:
            conn.sendall(f"No open ports found for {host}.\n".encode('utf-8'))
        except:
            pass

    return True  # We handled the command