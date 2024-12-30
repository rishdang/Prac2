#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>
#include "../client/client.h"

void test_connect_success(void **state) {
    (void) state;
    int result = connect_to_server("127.0.0.1", "8080");
    assert_int_equal(result, 0);
}

void test_connect_fail(void **state) {
    (void) state;
    int result = connect_to_server("invalid_host", "8080");
    assert_int_equal(result, -1);
}

int main(void) {
    const struct CMUnitTest tests[] = {
        cmocka_unit_test(test_connect_success),
        cmocka_unit_test(test_connect_fail),
    };
    return cmocka_run_group_tests(tests, NULL, NULL);
}