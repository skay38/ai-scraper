#!/bin/bash
# Pre-commit hook: blocks commit if checks fail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only intercept git commit commands
if [[ "$COMMAND" != *"git commit"* ]] && [[ "$COMMAND" != *"git-commit"* ]]; then
    exit 0
fi

cd "$CLAUDE_PROJECT_DIR" || exit 2

# Run all checks
echo "Running pre-commit checks..." >&2

# Format
if ! uv run ruff format --check . >/dev/null 2>&1; then
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Code is not formatted. Run /format first."}}'
    exit 0
fi

# Lint
LINT_OUTPUT=$(uv run ruff check . 2>&1)
if [ $? -ne 0 ]; then
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"Linting failed. Run /lint first.\n$LINT_OUTPUT\"}}"
    exit 0
fi

# Type check
TYPE_OUTPUT=$(uv run pyright . 2>&1)
if [ $? -ne 0 ]; then
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"Type check failed. Run /typecheck first.\n$TYPE_OUTPUT\"}}"
    exit 0
fi

# Tests
TEST_OUTPUT=$(uv run pytest 2>&1)
if [ $? -ne 0 ]; then
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"Tests failed. Run /test first.\n$TEST_OUTPUT\"}}"
    exit 0
fi

# All checks passed
exit 0
