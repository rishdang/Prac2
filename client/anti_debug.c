#include "anti_debug.h"

#ifdef __linux__
#include <sys/ptrace.h>
#endif
#include <signal.h>
#include <time.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void anti_debug_ptrace() {
#ifdef __linux__
    if (ptrace(PTRACE_TRACEME, 0, NULL, NULL) == -1) {
        printf("Debugger detected via ptrace! Exiting.\n");
        exit(EXIT_FAILURE);
    }
#else
    printf("ptrace is not supported on this platform. Skipping ptrace check.\n");
#endif
}

void anti_debug_proc() {
    FILE *fp = fopen("/proc/self/status", "r");
    if (!fp) {
        perror("Error opening /proc/self/status");
        return;
    }

    char line[256];
    int tracer_pid = 0;
    while (fgets(line, sizeof(line), fp)) {
        if (strncmp(line, "TracerPid:", 10) == 0) {
            tracer_pid = atoi(line + 10);
            break;
        }
    }
    fclose(fp);

    if (tracer_pid != 0) {
        // Combine with other anti-debug checks
        if (anti_debug_timing()) { // Assume anti_debug_timing exists
            printf("Debugger confirmed via /proc/self/status and timing! Exiting.\n");
            exit(EXIT_FAILURE);
        } else {
            printf("Warning: /proc/self/status suggests a debugger, but no timing anomaly detected.\n");
        }
    }
}

void anti_debug_timing() {
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (volatile int i = 0; i < 1000000; i++);

    clock_gettime(CLOCK_MONOTONIC, &end);
    long elapsed = (end.tv_sec - start.tv_sec) * 1000000000L + (end.tv_nsec - start.tv_nsec);

    printf("Timing check elapsed: %ld ns\n", elapsed); // Debug print for verification

    if (elapsed > 5000000) { // Adjusted threshold
        printf("Debugger detected based on timing! Exiting.\n");
        exit(EXIT_FAILURE);
    }
}

void signal_handler(int sig) {
    printf("Debugger detected via signal handling! Exiting.\n");
    exit(EXIT_FAILURE);
}

void anti_debug_signals() {
    signal(SIGTRAP, signal_handler);
    raise(SIGTRAP);
}

void anti_debug_ppid() {
    if (getppid() != 1) {
        printf("Debugger detected based on parent PID! Exiting.\n");
        exit(EXIT_FAILURE);
    }
}

void anti_debug_env() {
    const char *env_vars[] = {"LD_PRELOAD", "LD_LIBRARY_PATH", NULL};
    for (int i = 0; env_vars[i]; i++) {
        if (getenv(env_vars[i])) {
            printf("Debugger detected via environment variables! Exiting.\n");
            exit(EXIT_FAILURE);
        }
    }
}

void anti_debug_checksum() {
    FILE *file = fopen("/proc/self/exe", "rb");
    if (!file) return;

    unsigned char buffer[1024];
    size_t read_size;
    unsigned long checksum = 0;

    while ((read_size = fread(buffer, 1, sizeof(buffer), file)) > 0) {
        for (size_t i = 0; i < read_size; i++) {
            checksum += buffer[i];
        }
    }

    fclose(file);

    if (checksum != 0xDEADBEEF) {
        printf("Debugger detected via checksum mismatch! Exiting.\n");
        exit(EXIT_FAILURE);
    }
}

void anti_debug_process() {
    system("ps aux | grep gdb | grep -v grep > /dev/null && echo 'Debugger detected!' && exit 1");
}

void perform_anti_debug_checks() {
    anti_debug_ptrace();
    anti_debug_proc();
    anti_debug_timing();
    anti_debug_signals();
    anti_debug_ppid();
    anti_debug_env();
    anti_debug_checksum();
    anti_debug_process();
}