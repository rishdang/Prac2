## Intro

Pra-C2 is a thing that I wrote just for lulz, during a long winter night. 

Bored of existing C2? Want to test your EDR capabilities? Need a somewhat working codebase for your ToyC2? Need to scare the blueteam with an unknown C2 which no one uses? Getting a good night sleep knowing your existing C2 works fine? 

Well you'have come to the right place.

## Features :

### MULTIPLE types of clients. 
* One with **Very unstable** process hollowing support (client_proc_h.c) thanks to brilliant tutorial by Jeffrey Bencteux here https://www.bencteux.fr/posts/linux_process_hollowing/.
* And one without, but a bit more stable (client.c)
* Added one experimental keylogger as well : client_k.c
* Added experimental ransomware module (currently local only) : client_r.c
* Usage: ./client [-i <ip/domain>] [-p <port>] [-w <password>]

### PYTHON based Server 
```
└── Server code consists of banner for ascii art and MOTD if you wish. 
--> client_commands consists of command for running at client end, to be honest, it seemed like a good idea at first but it is not. I may combine it with client_management. Read on..
--> client_management is the actual place where client communication happens, this is filled with too many comments I wrote to understand and remember what I am doing.
--> admin_server consists of admin code for running the server, also seemed lie a good idea at first but I may combine and refactor it.
```

### Modular capabilities 

```
└── capabilities consists of modular plugins, and extensions via which you can extend the C2.
```
### C based Client.
```
└── client consists of POSIX compliant C code which can interact with server and provides command execution capabilities.
└── Modular capabilities, has basic anti-debug, post exploitation and stealth capabilities as well.

```
### LOCAL roles
* Admin works on port 9999 or the one you wish to define.
* Operators works on port 20022, will fix it to a different port later.

### Remote role/ C2 comms
* works on port 27015 or a custom one, server will ask you for it.
* default C2 authentication is password based, will fix it later to a timed hash based one. Default password is "mysecretpass1" without quotes

## Architecture : 

Main server runs from Prac2_Server.py. It is a plugin based, highly modular C2. 

```
Prac2/
├── Prac2_Server.py
├── server_code/ 
│   ├── __init__.py
│   ├── admin_server.py         # Main server code
│   ├── banner.py               # Banner
│   ├── client_commands.py      # client commands here 
│   └── client_management.py    # client functional management
|   └── etc.. etc..
└── capabilities/
|   ├── __init__.py
|   ├── multi_client_support.py
|   ├── tls_support.py
|   └── <other_plugins etc etc>.py
└── client/
|   ├── client.c                # Main client code point
|   ├── client_base.h           # base capabilities and function logic
|   ├── network.c               # Networking logic (server connection, authentication)
|   ├── shell_exec.c            # Shell command execution logic
|   ├── Makefile                # add remove things if required
|   ├── other capability specific files.
|   └── old clients
|       └── old clients, client_k.c, client_old.c, client_r.c etc
└── tests/
    └── unit tests (incomplete, i know)
```

I know a lot can be refactored here, but at this point I just want to see how far I can push this from a concept PoV. Consider this as a hobby C2 code so that I can polish my rusty C and Python skills along with paradigms. At this point in time, it works on my machine. If it doesn't works on yours, you are out of luck. 
I might be maintaining a private repository of stable code which I may release in future if it looks and functions okay.

Have inputs? Need to submit enhancements? Need some guidance? 
Reach me out on dangwal<at>rish<dot>one.