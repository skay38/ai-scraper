---
name: lint
description: Run ruff linter with auto-fix on the codebase
user-invocable: true
allowed-tools:
  - Bash
---

# Lint

Run the ruff linter with auto-fix on the project.

Execute:
```bash
uv run ruff check --fix .
```

Report any remaining issues that couldn't be auto-fixed.
