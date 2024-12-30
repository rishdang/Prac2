# server_code/banner.py

BANNER_ART = r"""

██████╗ ██████╗  █████╗        ██████╗██████╗ 
██╔══██╗██╔══██╗██╔══██╗      ██╔════╝╚════██╗
██████╔╝██████╔╝███████║█████╗██║      █████╔╝
██╔═══╝ ██╔══██╗██╔══██║╚════╝██║     ██╔═══╝ 
██║     ██║  ██║██║  ██║      ╚██████╗███████╗
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝       ╚═════╝╚══════╝

PRA-C2 version 0.1Alpha                                       
"""

def show_startup_banner():
    """
    Print the ASCII banner to the console at server startup.
    """
    print(BANNER_ART)

def get_admin_banner() -> str:
    """
    Returns the ASCII banner text plus a welcome note,
    used when an admin session is established.
    """
    return f"--- Admin Connection Established ---\n{BANNER_ART}"

def get_operator_banner() -> str:
    """
    Returns ASCII art or any text you'd like to display
    when the operator shell session starts.
    """
    return f"--- Operator Connection Established ---\n{BANNER_ART}"