#!/bin/bash
# Claude Code Hook: Run tests after coding and flag broken tests
# Triggered by the Stop hook when Claude finishes responding

set -o pipefail

cd "$CLAUDE_PROJECT_DIR" || exit 0

# Parse the hook input to check if code was modified
STDIN_DATA=$(cat)
TRANSCRIPT=$(echo "$STDIN_DATA" | jq -r '.transcript // empty' 2>/dev/null)

# Check if any Write or Edit tools were used in this response
if echo "$TRANSCRIPT" | grep -qE '"tool":\s*"(Write|Edit)"'; then
    CODE_MODIFIED=true
else
    CODE_MODIFIED=false
fi

# Only run tests if code was modified
if [ "$CODE_MODIFIED" = false ]; then
    exit 0
fi

echo "========================================" >&2
echo "Running tests after code changes..." >&2
echo "========================================" >&2

# Run Django tests with failfast to stop on first failure
TEST_OUTPUT=$(poetry run python manage.py test --failfast 2>&1)
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "" >&2
    echo "All tests passed!" >&2
    echo "========================================" >&2
    exit 0
else
    echo "" >&2
    echo "TESTS FAILED!" >&2
    echo "========================================" >&2
    echo "" >&2

    # Extract and display failure information
    echo "$TEST_OUTPUT" | tail -50 >&2

    echo "" >&2
    echo "========================================" >&2
    echo "Please fix the failing tests above." >&2
    echo "========================================" >&2

    # Exit with code 2 to block and show error to Claude
    exit 2
fi
