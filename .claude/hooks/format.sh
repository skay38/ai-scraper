#!/bin/bash
# Auto-format hook: runs ruff format on modified Python files

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty')

# Only process Python files
if [[ "$FILE_PATH" == *.py ]]; then
    cd "$CLAUDE_PROJECT_DIR" || exit 0
    uv run ruff format "$FILE_PATH" 2>/dev/null
fi

exit 0
