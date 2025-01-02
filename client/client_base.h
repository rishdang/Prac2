#ifndef CLIENT_BASE_H
#define CLIENT_BASE_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <errno.h>
#include <getopt.h>

#define DEFAULT_SERVER_PORT "8080"
#define DEFAULT_SERVER_IP "127.0.0.1"
#define BUFFER_SIZE 1024

// Function prototypes
void error_exit(const char *message);
void print_usage(const char *prog_name);
const char *get_shell();
void execute_command_and_send_output(const char *command, int sockfd);
int authenticate(int sockfd, const char *cmd_line_password);
void error_exit(const char *message);

#endif