#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <errno.h>

#define DEFAULT_SERVER_PORT 27015   // Default client port
#define DEFAULT_SERVER_IP "127.0.0.1" // Default server IP
#define BUFFER_SIZE 1024            // Size of the read/write buffer

void error_exit(const char *message) {
    perror(message);
    exit(EXIT_FAILURE);
}

void execute_command_and_send_output(const char *command, int sockfd) {
    char output_buffer[BUFFER_SIZE];
    FILE *fp;

    fp = popen(command, "r");
    if (fp == NULL) {
        snprintf(output_buffer, BUFFER_SIZE, "Failed to execute command: %s\n", command);
        send(sockfd, output_buffer, strlen(output_buffer), 0);
        snprintf(output_buffer, BUFFER_SIZE, "[END_OF_OUTPUT]\n");
        send(sockfd, output_buffer, strlen(output_buffer), 0);  // Ensure end marker is sent even on failure
        return;
    }

    // Read command output line by line and send it to the server
    while (fgets(output_buffer, sizeof(output_buffer), fp) != NULL) {
        if (send(sockfd, output_buffer, strlen(output_buffer), 0) < 0) {
            // Stop sending if the connection is broken
            perror("Connection broken while sending output");
            break;
        }
        usleep(1000);  // Add slight delay for real-time processing
    }

    pclose(fp);

    // Send the end marker to indicate completion of output
    snprintf(output_buffer, BUFFER_SIZE, "[END_OF_OUTPUT]\n");
    send(sockfd, output_buffer, strlen(output_buffer), 0);
}

int authenticate(int sockfd) {
    char password[BUFFER_SIZE];
    char recv_buffer[BUFFER_SIZE];
    ssize_t received;

    // Prompt user for password
    printf("Enter server password: ");
    if (fgets(password, BUFFER_SIZE, stdin) == NULL) {
        fprintf(stderr, "Failed to read password.\n");
        return 0;
    }

    password[strcspn(password, "\n")] = '\0'; // Remove newline character

    // Send password to server
    if (send(sockfd, password, strlen(password), 0) < 0) {
        perror("Failed to send password");
        return 0;
    }

    // Wait for authentication response
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

int main() {
    int sockfd;
    struct sockaddr_in server_addr;
    char send_buffer[BUFFER_SIZE];
    char recv_buffer[BUFFER_SIZE];
    char server_ip[BUFFER_SIZE];
    int server_port = DEFAULT_SERVER_PORT;

    // Prompt for server IP
    printf("Enter server IP (default: %s): ", DEFAULT_SERVER_IP);
    if (fgets(server_ip, BUFFER_SIZE, stdin) == NULL || server_ip[0] == '\n') {
        strcpy(server_ip, DEFAULT_SERVER_IP);
    } else {
        server_ip[strcspn(server_ip, "\n")] = '\0';
    }

    // Prompt for server port
    printf("Enter server port (default: %d): ", DEFAULT_SERVER_PORT);
    char port_input[BUFFER_SIZE];
    if (fgets(port_input, BUFFER_SIZE, stdin) != NULL && port_input[0] != '\n') {
        server_port = atoi(port_input);
        if (server_port <= 0 || server_port > 65535) {
            fprintf(stderr, "Invalid port. Using default port %d.\n", DEFAULT_SERVER_PORT);
            server_port = DEFAULT_SERVER_PORT;
        }
    }

    // Create socket
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        error_exit("Socket creation failed");
    }

    // Configure server address
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(server_port);
    if (inet_pton(AF_INET, server_ip, &server_addr.sin_addr) <= 0) {
        error_exit("Invalid server IP address");
    }

    // Connect to the server
    if (connect(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        error_exit("Connection to server failed");
    }
    printf("Connected to server at %s:%d\n", server_ip, server_port);

    // Authenticate before proceeding
    if (!authenticate(sockfd)) {
        close(sockfd);
        return 1;
    }

    // Main loop for receiving commands and sending output
    while (1) {
        ssize_t received = recv(sockfd, recv_buffer, BUFFER_SIZE - 1, 0);
        if (received < 0) {
            perror("Receive failed");
            break;
        } else if (received == 0) {
            printf("Server closed the connection.\n");
            break;
        }

        recv_buffer[received] = '\0';

        // Exit client on "exit" or "quit"
        if (strcmp(recv_buffer, "exit") == 0 || strcmp(recv_buffer, "quit") == 0) {
            printf("Exiting on server request...\n");
            break;
        }

        // Execute command and send output
        printf("Executing command: %s\n", recv_buffer);
        execute_command_and_send_output(recv_buffer, sockfd);
    }

    // Clean up
    close(sockfd);
    printf("Disconnected from server.\n");
    return 0;
}