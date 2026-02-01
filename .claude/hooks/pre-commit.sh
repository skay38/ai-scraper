#!/bin/bash
# Pre-commit hook: blocks commit if checks fail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null) || exit 0

# Only intercept git commit commands
if [[ -z "$COMMAND" ]] || { [[ "$COMMAND" != *"git commit"* ]] && [[ "$COMMAND" != *"git-commit"* ]]; }; then
    exit 0
fi

cd "$CLAUDE_PROJECT_DIR" || exit 2

# Helper to escape JSON strings properly
json_escape() {
    python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))"
}

# Run all checks
echo "Running pre-commit checks..." >&2

# Format check
if ! uv run ruff format --check . >/dev/null 2>&1; then
    REASON="Code is not formatted. Run /format first."
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":$(echo "$REASON" | json_escape)}}"
    exit 0
fi

# Lint check
LINT_OUTPUT=$(uv run ruff check . 2>&1)
if [ $? -ne 0 ]; then
    REASON="Linting failed. Run /lint first."$'\n'"$LINT_OUTPUT"
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":$(echo "$REASON" | json_escape)}}"
    exit 0
fi

# Type check
TYPE_OUTPUT=$(uv run pyright . 2>&1)
if [ $? -ne 0 ]; then
    REASON="Type check failed. Run /typecheck first."$'\n'"$TYPE_OUTPUT"
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":$(echo "$REASON" | json_escape)}}"
    exit 0
fi

# Tests (skip if no tests exist)
TEST_OUTPUT=$(uv run pytest 2>&1)
TEST_EXIT=$?
if [ $TEST_EXIT -ne 0 ]; then
    # Allow if no tests were collected (exit code 5 = no tests collected)
    if [ $TEST_EXIT -eq 5 ] || echo "$TEST_OUTPUT" | grep -q "no tests ran\|collected 0 items"; then
        : # No tests to run, continue
    else
        REASON="Tests failed. Run /test first."$'\n'"$TEST_OUTPUT"
        echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":$(echo "$REASON" | json_escape)}}"
        exit 0
    fi
fi

# All checks passed
exit 0
