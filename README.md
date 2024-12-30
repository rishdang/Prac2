Pra-C2 is a thing that I wrote just for lulz, during a long winter night. The code is somewhat messy, but it works.
Too many comments, AI assisted (thanks, Co-Pilot) but not AI written. I observed a lot of issues in AI code and found it introduced new issues instead of fixing some. 

Architecture : 

Main server runs from Prac2_Server.py. It is a plugin based, highly modular C2. 

Three roles :

```
LOCAL ones
--> Admin works on port 9999 or the one you wish to define.
--> Operators works on port 20022, will fix it to a different port later.

POSIX compliant REMOTE or C2 one
--> works on port 27015 or a custom one, server will ask you for it.
--> default C2 authentication is password based, will fix it later to a timed hash based one. Default password is "mysecretpass1" without quotes
--> Two type of clients. 
    --> One with **Very unstable** process hollowing support (client_proc_h.c) thanks to brilliant tutorial by Jeffrey Bencteux here https://www.bencteux.fr/posts/linux_process_hollowing/.
    --> And one without, but a bit more stable (client.c)
--> Usage: ./client [-i <ip/domain>] [-p <port>] [-w <password>]
```
The code tree looks like this :

```
Prac2/
├── Prac2_Server.py
├── server_code/ 
│   ├── __init__.py
│   ├── admin_server.py
│   ├── banner.py
│   ├── client_commands.py
│   └── client_management.py
|   └── etc.. etc..
└── capabilities/
    ├── __init__.py
    ├── multi_client_support.py
    ├── tls_support.py
    └── <other_plugins etc etc>.py
└── client/
    ├──client.c
    └── etc etc..
```
PYTHON based Server 
```
└── Server code consists of banner for ascii art and MOTD if you wish. 
--> client_commands consists of command for running at client end, to be honest, it seemed like a good idea at first but it is not. I may combine it with client_management. Read on..
--> client_management is the actual place where client communication happens, this is filled with too many comments I wrote to understand and remember what I am doing.
--> admin_server consists of admin code for running the server, also seemed lie a good idea at first but I may combine and refactor it.
```
```
└── capabilities consists of modular plugins, and extensions via which you can extend the C2.
```
C based Client.
```
└── client consists of POSIX compliant C code which can interact with server and provides command execution capabilities.
```
I know a lot can be refactored here, but at this point I just want to see how far I can push this from a concept PoV. Consider this as a hobby C2 code so that I can polish my rusty C and Python skills along with paradigms.
