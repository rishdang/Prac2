#ifndef ANTI_DEBUG_H
#define ANTI_DEBUG_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>

#ifdef __linux__
#include <sys/ptrace.h>
#endif

// Function prototypes
void anti_debug_ptrace();     // Detect debugger via ptrace (Linux only)
void anti_debug_proc();       // Detect debugger via /proc/self/status
//int anti_debug_timing();     // Detect debugger via timing discrepancies
void anti_debug_signals();  Detect debugger via signal handling, disabling it for now since it is causing issues on Mac
void anti_debug_ppid();       // Detect debugger via parent process ID
void anti_debug_env();        // Detect debugger via environment variables
void anti_debug_checksum();   // Detect debugger via checksum verification
void anti_debug_process();    // Detect debugger via running processes
void perform_anti_debug_checks(); // Perform all anti-debugging checks

#endif