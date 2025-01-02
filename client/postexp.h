#ifndef POSTEXP_H
#define POSTEXP_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

// Function prototypes
void start_keylogging(const char *output_file);
void stop_keylogging();
void capture_screenshot(const char *output_file);
void lateral_movement(const char *target_ip, const char *command);

#endif