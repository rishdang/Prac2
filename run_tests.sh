#!/bin/bash

echo "Running python unit tests..."
python3 -m unittest discover -s tests

echo "Compiling and running C tests..."
for test_file in tests/*.c; do
    gcc -o "${test_file%.c}" "$test_file" -lcmocka
    ./"${test_file%.c}"
done

echo "All tests completed."