#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>
#include "../client/client.h"

void test_connect_to_server_success(void **state) {
    (void) state; // Unused
    assert_int_equal(connect_to_server("127.0.0.1", 8080), 0);
}

void test_connect_to_server_failure(void **state) {
    (void) state; // Unused
    assert_int_equal(connect_to_server("192.168.1.1", 8080), -1);
    assert_int_equal(connect_to_server("127.0.0.1", 1234), -1);
}

int main(void) {
    const struct CMUnitTest tests[] = {
        cmocka_unit_test(test_connect_to_server_success),
        cmocka_unit_test(test_connect_to_server_failure),
    };
    return cmocka_run_group_tests(tests, NULL, NULL);
}