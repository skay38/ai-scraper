---
name: test
description: Run pytest on the codebase
user-invocable: true
allowed-tools:
  - Bash
---

# Test

Run pytest on the project with coverage.

Execute:
```bash
uv run pytest --cov --cov-report=term-missing
```

Report test results including any failures and coverage summary.
