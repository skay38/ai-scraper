#!/bin/bash
# PostToolUse hook: check for common guideline violations after writing Python files

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only check Python source files (not tests, not __init__)
if [[ "$FILE_PATH" != *.py ]] || [[ "$FILE_PATH" == *test_* ]] || [[ "$FILE_PATH" == *_test.py ]] || [[ "$FILE_PATH" == *__init__* ]]; then
    exit 0
fi

cd "$CLAUDE_PROJECT_DIR" || exit 0

WARNINGS=""

# Check for print() statements (excluding comments)
if grep -n "^\s*print(" "$FILE_PATH" 2>/dev/null | grep -v "^\s*#" | head -5 | grep -q .; then
    LINES=$(grep -n "^\s*print(" "$FILE_PATH" 2>/dev/null | grep -v "^\s*#" | head -5 | cut -d: -f1 | tr '\n' ',' | sed 's/,$//')
    WARNINGS="${WARNINGS}WARNING: print() found at lines $LINES - use logger instead.\n"
fi

# Check for generic exception handling (except Exception, except ValueError, etc.)
if grep -nE "except\s+(Exception|ValueError|TypeError|RuntimeError|KeyError)\s*:" "$FILE_PATH" 2>/dev/null | head -3 | grep -q .; then
    LINES=$(grep -nE "except\s+(Exception|ValueError|TypeError|RuntimeError|KeyError)\s*:" "$FILE_PATH" 2>/dev/null | head -3 | cut -d: -f1 | tr '\n' ',' | sed 's/,$//')
    WARNINGS="${WARNINGS}WARNING: Generic exception at lines $LINES - use custom exceptions in business logic.\n"
fi

# Check for functions missing type annotations (basic heuristic)
if grep -nE "^\s*def\s+\w+\([^)]*\)\s*:" "$FILE_PATH" 2>/dev/null | grep -v "->" | head -3 | grep -q .; then
    LINES=$(grep -nE "^\s*def\s+\w+\([^)]*\)\s*:" "$FILE_PATH" 2>/dev/null | grep -v "->" | head -3 | cut -d: -f1 | tr '\n' ',' | sed 's/,$//')
    WARNINGS="${WARNINGS}WARNING: Functions at lines $LINES may be missing return type annotations.\n"
fi

# Check for untyped empty collections
if grep -nE "^\s*\w+\s*=\s*\[\]$|^\s*\w+\s*=\s*\{\}$" "$FILE_PATH" 2>/dev/null | head -3 | grep -q .; then
    LINES=$(grep -nE "^\s*\w+\s*=\s*\[\]$|^\s*\w+\s*=\s*\{\}$" "$FILE_PATH" 2>/dev/null | head -3 | cut -d: -f1 | tr '\n' ',' | sed 's/,$//')
    WARNINGS="${WARNINGS}WARNING: Untyped empty collection at lines $LINES - use explicit types like 'items: list[str] = []'.\n"
fi

if [ -n "$WARNINGS" ]; then
    # Return as additionalContext so Claude sees the warnings
    ESCAPED=$(echo -e "$WARNINGS" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))")
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUse\",\"additionalContext\":$ESCAPED}}"
fi

exit 0
