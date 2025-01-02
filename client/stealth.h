#ifndef STEALTH_H
#define STEALTH_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

// Function prototypes
void rename_process(const char *new_name);
void change_cmdline(const char *new_cmdline);
void clean_artifacts();
void dynamic_sleep(int base_time, int jitter);

#endif