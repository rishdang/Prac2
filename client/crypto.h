#ifndef CRYPTO_H
#define CRYPTO_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>

#define BUFFER_SIZE 1024

void xor_encrypt(const char *key, unsigned char *data, size_t data_len);
void process_file(const char *file_path, const char *key, int decrypt_mode);
void process_directory(const char *directory_path, const char *key, int decrypt_mode);

#endif