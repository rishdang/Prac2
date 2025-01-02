all: client

client: client.c network.c shell_exec.c crypto.c
	gcc -o client client.c network.c shell_exec.c crypto.c anti_debug.c -Wall -D_POSIX_C_SOURCE=200809L -D_XOPEN_SOURCE=700

clean:
	rm -f client