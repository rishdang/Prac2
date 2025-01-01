all: client

client: client.c network.c shell_exec.c crypto.c
	gcc -o client client.c network.c shell_exec.c crypto.c -Wall

clean:
	rm -f client