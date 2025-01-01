#ifndef CRYPTO_H
#define CRYPTO_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>
#include "client_base.h"

// Function prototypes
void xor_encrypt(const char *key, unsigned char *data, size_t data_len);
void process_file(const char *file_path, const char *key);
void process_directory(const char *directory_path, const char *key);

#endif