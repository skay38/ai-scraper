---
name: typecheck
description: Run pyright type checker on the codebase
user-invocable: true
allowed-tools:
  - Bash
---

# Type Check

Run pyright type checker on the project.

Execute:
```bash
uv run pyright .
```

Report any type errors found.
