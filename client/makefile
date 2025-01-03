# Add remove modules (abc.c) as required.
all: client

#Disabling anti debug and stealth options since they are pretty buggy
client: client.c client_base.c crypto.c anti_debug.c stealth.c postexp.c command_handler.c
	gcc -o client client.c client_base.c crypto.c anti_debug.c stealth.c postexp.c command_handler.c -Wall -D_POSIX_C_SOURCE=200809L -D_XOPEN_SOURCE=700

#client: client.c client_base.c crypto.c postexp.c
#	gcc -o client client.c client_base.c crypto.c postexp.c -Wall -D_POSIX_C_SOURCE=200809L -D_XOPEN_SOURCE=700

clean:
	rm -f client