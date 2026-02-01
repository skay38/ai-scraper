#!/bin/bash
# Auto-fix hook: runs ruff format + lint fix on modified Python files

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty')

# Only process Python files
if [[ "$FILE_PATH" == *.py ]]; then
    cd "$CLAUDE_PROJECT_DIR" || exit 0

    # Format first
    uv run ruff format "$FILE_PATH" 2>/dev/null

    # Then lint with auto-fix (fixes import sorting, unused imports, etc.)
    uv run ruff check --fix "$FILE_PATH" 2>/dev/null
fi

exit 0
