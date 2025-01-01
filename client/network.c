#include "client_base.h"

void error_exit(const char *message) {
    perror(message);
    exit(EXIT_FAILURE);
}

void print_usage(const char *prog_name) {
    fprintf(stderr, "Usage: %s [-i <ip/domain>] [-p <port>] [-w <password>]\n", prog_name);
}

int authenticate(int sockfd, const char *cmd_line_password) {
    char recv_buffer[BUFFER_SIZE];
    ssize_t received;

    if (send(sockfd, cmd_line_password, strlen(cmd_line_password), 0) < 0) {
        perror("Failed to send password");
        return 0;
    }

    received = recv(sockfd, recv_buffer, BUFFER_SIZE - 1, 0);
    if (received < 0) {
        perror("Failed to receive authentication response");
        return 0;
    }

    recv_buffer[received] = '\0';
    if (strcmp(recv_buffer, "REMOTE_SHELL_CONFIRMED\n") == 0) {
        printf("Authentication successful.\n");
        return 1;
    } else {
        printf("Authentication failed: %s\n", recv_buffer);
        return 0;
    }
}