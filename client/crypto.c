#include "crypto.h"

void xor_encrypt(const char *key, unsigned char *data, size_t data_len) {
    size_t key_len = strlen(key);
    for (size_t i = 0; i < data_len; i++) {
        data[i] ^= key[i % key_len];
    }
}

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