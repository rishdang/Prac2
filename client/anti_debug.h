#ifndef ANTI_DEBUG_H
#define ANTI_DEBUG_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ptrace.h>
#include <signal.h>
#include <time.h>
#include <dirent.h>

// Function prototypes
void anti_debug_ptrace();
void anti_debug_proc();
void anti_debug_timing();
void anti_debug_signals();
void anti_debug_ppid();
void anti_debug_env();
void anti_debug_checksum();
void anti_debug_process();
void perform_anti_debug_checks();

#endif