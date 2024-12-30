#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>
#include "../client/client.h"

// Mocked function for socket creation
int __wrap_socket(int domain, int type, int protocol) {
    return mock_type(int);
}

// Mocked function for connecting to a server
int __wrap_connect(int sockfd, const struct sockaddr *addr, socklen_t addrlen) {
    return mock_type(int);
}

// Test for successful connection
static void test_connect_to_server_success(void **state) {
    (void) state; // Unused

    // Mock socket creation and connection to succeed
    will_return(__wrap_socket, 3); // Mock socket descriptor
    will_return(__wrap_connect, 0); // Success

    int result = connect_to_server("127.0.0.1", 8080);
    assert_int_equal(result, 0);
}

// Test for invalid IP address
static void test_connect_to_server_invalid_ip(void **state) {
    (void) state; // Unused

    // Mock socket creation to fail
    will_return(__wrap_socket, -1); // Failure

    int result = connect_to_server("invalid_ip", 8080);
    assert_int_equal(result, -1);
}

// Test for unreachable port
static void test_connect_to_server_unreachable_port(void **state) {
    (void) state; // Unused

    // Mock socket creation to succeed but connection to fail
    will_return(__wrap_socket, 3); // Mock socket descriptor
    will_return(__wrap_connect, -1); // Failure

    int result = connect_to_server("127.0.0.1", 9999);
    assert_int_equal(result, -1);
}

int main(void) {
    const struct CMUnitTest tests[] = {
        cmocka_unit_test(test_connect_to_server_success),
        cmocka_unit_test(test_connect_to_server_invalid_ip),
        cmocka_unit_test(test_connect_to_server_unreachable_port),
    };
    return cmocka_run_group_tests(tests, NULL, NULL);
}