#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>
#include "../client/client_proc_h.h"

// Mocked function for ptrace
int __wrap_ptrace(enum __ptrace_request request, pid_t pid, void *addr, void *data) {
    return mock_type(int);
}

// Test for successful process hollowing
static void test_hollow_process_success(void **state) {
    (void) state; // Unused

    // Mock ptrace calls to succeed
    will_return(__wrap_ptrace, 0); // Success for all ptrace calls

    int result = hollow_process("/bin/ls", "payload");
    assert_int_equal(result, 0);
}

// Test for invalid target process
static void test_hollow_process_invalid_target(void **state) {
    (void) state; // Unused

    // Mock ptrace calls to fail
    will_return(__wrap_ptrace, -1); // Failure for ptrace attach

    int result = hollow_process("/invalid/target", "payload");
    assert_int_equal(result, -1);
}

// Test for invalid payload
static void test_hollow_process_invalid_payload(void **state) {
    (void) state; // Unused

    // Mock ptrace calls to fail during payload injection
    will_return(__wrap_ptrace, 0);  // Success for ptrace attach
    will_return(__wrap_ptrace, -1); // Failure for ptrace write

    int result = hollow_process("/bin/ls", "invalid_payload");
    assert_int_equal(result, -1);
}

int main(void) {
    const struct CMUnitTest tests[] = {
        cmocka_unit_test(test_hollow_process_success),
        cmocka_unit_test(test_hollow_process_invalid_target),
        cmocka_unit_test(test_hollow_process_invalid_payload),
    };
    return cmocka_run_group_tests(tests, NULL, NULL);
}