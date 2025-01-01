#include "client_base.h"

int main(int argc, char *argv[]) {
    int sockfd, opt;
    char server_ip[BUFFER_SIZE] = DEFAULT_SERVER_IP;
    char server_port[BUFFER_SIZE] = DEFAULT_SERVER_PORT;
    char password[BUFFER_SIZE] = "";

    struct addrinfo hints, *res, *p;

    while ((opt = getopt(argc, argv, "i:p:w:")) != -1) {
        switch (opt) {
            case 'i':
                strncpy(server_ip, optarg, BUFFER_SIZE);
                break;
            case 'p':
                strncpy(server_port, optarg, BUFFER_SIZE);
                break;
            case 'w':
                strncpy(password, optarg, BUFFER_SIZE);
                break;
            default:
                print_usage(argv[0]);
                exit(EXIT_FAILURE);
        }
    }

    if (strlen(password) == 0) {
        fprintf(stderr, "Error: Password is required.\n");
        print_usage(argv[0]);
        exit(EXIT_FAILURE);
    }

    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(server_ip, server_port, &hints, &res) != 0) {
        error_exit("Error resolving server address");
    }

    for (p = res; p != NULL; p = p->ai_next) {
        sockfd = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
        if (sockfd < 0) continue;

        if (connect(sockfd, p->ai_addr, p->ai_addrlen) == 0) break;

        close(sockfd);
    }

    if (!p) {
        fprintf(stderr, "Error: Unable to connect to server at %s:%s\n", server_ip, server_port);
        freeaddrinfo(res);
        exit(EXIT_FAILURE);
    }

    freeaddrinfo(res);
    printf("Connected to server at %s:%s\n", server_ip, server_port);

    if (!authenticate(sockfd, password)) {
        close(sockfd);
        return 1;
    }

    printf("Enter commands to execute on the server. Type 'exit' to quit.\n");
    char command[BUFFER_SIZE];
    while (1) {
        printf("> ");
        if (!fgets(command, BUFFER_SIZE, stdin)) break;
        command[strcspn(command, "\n")] = '\0';
        if (strcmp(command, "exit") == 0) break;
        execute_command_and_send_output(command, sockfd);
    }

    close(sockfd);
    return 0;
}