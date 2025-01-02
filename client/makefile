all: client

client: client.c crypto.c anti_debug.c stealth.c postexp.c
	gcc -o client client.c crypto.c anti_debug.c stealth.c postexp.c -Wall -D_POSIX_C_SOURCE=200809L -D_XOPEN_SOURCE=700

clean:
	rm -f client