all: client

client: client.c network.c shell_exec.c
	gcc -o client client.c network.c shell_exec.c -Wall

clean:
	rm -f client