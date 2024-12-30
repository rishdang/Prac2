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

void launch_shell() {
    printf("Spawning a local shell...\n");
    char *args[] = {"/bin/sh", NULL};
    execve("/bin/sh", args, NULL);
    perror("Failed to execute shell");
    exit(EXIT_FAILURE);
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
        strcpy(server_ip, DEFAULT_SERVER_IP); // Use default if input is empty
    } else {
        server_ip[strcspn(server_ip, "\n")] = '\0'; // Remove newline
    }

    // Prompt for server port
    printf("Enter server port (default: %d): ", DEFAULT_SERVER_PORT);
    char port_input[BUFFER_SIZE];
    if (fgets(port_input, BUFFER_SIZE, stdin) != NULL && port_input[0] != '\n') {
        server_port = atoi(port_input); // Convert input to integer
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

    // Main loop for sending/receiving data
    while (1) {
        printf("> ");
        if (fgets(send_buffer, BUFFER_SIZE, stdin) == NULL) {
            printf("Input error\n");
            break;
        }

        // Remove newline character
        size_t len = strlen(send_buffer);
        if (len > 0 && send_buffer[len - 1] == '\n') {
            send_buffer[len - 1] = '\0';
        }

        // Exit client on "exit" or "quit"
        if (strcmp(send_buffer, "exit") == 0 || strcmp(send_buffer, "quit") == 0) {
            printf("Exiting...\n");
            send(sockfd, send_buffer, strlen(send_buffer), 0); // Notify server
            break;
        }

        // Launch local shell on "shell" command
        if (strcmp(send_buffer, "shell") == 0) {
            launch_shell();
            continue;
        }

        // Send command to server
        if (send(sockfd, send_buffer, strlen(send_buffer), 0) < 0) {
            perror("Send failed");
            break;
        }

        // Receive response from server
        ssize_t received = recv(sockfd, recv_buffer, BUFFER_SIZE - 1, 0);
        if (received < 0) {
            perror("Receive failed");
            break;
        } else if (received == 0) {
            printf("Server closed the connection.\n");
            break;
        }

        // Null-terminate and print the response
        recv_buffer[received] = '\0';
        printf("%s\n", recv_buffer);
    }

    // Clean up
    close(sockfd);
    printf("Disconnected from server.\n");
    return 0;
}