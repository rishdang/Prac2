#ifndef COMMAND_HANDLER_H
#define COMMAND_HANDLER_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define BUFFER_SIZE 1024

// Function prototypes
void execute_and_send_command(int sockfd, const char *command, const char *shell);
void send_end_of_response(int sockfd);

#endif // COMMAND_HANDLER_H