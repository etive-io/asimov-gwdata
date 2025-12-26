#!/bin/bash
# run_tests.sh - Script to run asimov-gwdata tests
#
# This script demonstrates different ways to run the test suite.

set -e  # Exit on error

echo "========================================="
echo "asimov-gwdata Test Suite"
echo "========================================="
echo ""

# Check if package is installed
if ! python3 -c "import datafind" 2>/dev/null; then
    echo "Error: asimov-gwdata not installed"
    echo "Run: pip install -e ."
    exit 1
fi

echo "Package installed: OK"
echo ""

# Function to run tests and count results
run_test_suite() {
    local description="$1"
    local command="$2"
    
    echo "========================================="
    echo "$description"
    echo "========================================="
    echo "Command: $command"
    echo ""
    
    if eval "$command"; then
        echo ""
        echo "✓ $description: PASSED"
        echo ""
    else
        echo ""
        echo "✗ $description: FAILED"
        echo ""
        return 1
    fi
}

# Run different test suites
echo "Running test suites..."
echo ""

# 1. All tests (offline friendly)
run_test_suite \
    "All tests (offline mode)" \
    "python3 -m unittest discover -s tests -p 'test_*.py' -v"

# 2. Just the mock fixture tests
run_test_suite \
    "Mock fixture tests" \
    "python3 -m unittest tests.test_with_mocks -v"

# 3. Mock-based frame tests
run_test_suite \
    "Mock-based frame tests" \
    "python3 -m unittest tests.test_frames.TestLIGOFramesWithMocks -v"

# 4. Calibration tests (mostly mocked)
run_test_suite \
    "Calibration tests" \
    "python3 -m unittest tests.test_calibration.CalibrationDataTests -v"

echo "========================================="
echo "Test Summary"
echo "========================================="
echo "All test suites completed successfully!"
echo ""
echo "The test suite is designed to work without:"
echo "  - Network access"
echo "  - GWOSC servers"
echo "  - gwdatafind servers"  
echo "  - Downloaded test data files"
echo ""
echo "Tests requiring these resources skip gracefully."
echo ""
echo "For more information, see:"
echo "  - docs/testing.md"
echo "  - docs/ci-testing-examples.md"
echo "  - tests/README.md"
echo "========================================="
