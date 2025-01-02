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
    FILE *file = fopen("/proc/self/status", "r");
    if (!file) return;

    char line[256];
    while (fgets(line, sizeof(line), file)) {
        if (strncmp(line, "TracerPid:", 10) == 0) {
            int tracer_pid = atoi(line + 10);
            if (tracer_pid != 0) {
                printf("Debugger detected via /proc/self/status! Exiting.\n");
                fclose(file);
                exit(EXIT_FAILURE);
            }
        }
    }

    fclose(file);
}

void anti_debug_timing() {
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (volatile int i = 0; i < 1000000; i++);

    clock_gettime(CLOCK_MONOTONIC, &end);
    long elapsed = end.tv_nsec - start.tv_nsec;

    if (elapsed > 1000000) {
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