---
name: check
description: Run all checks (format, lint, typecheck, test) on the codebase
user-invocable: true
allowed-tools:
  - Bash
  - Skill
---

# Check

Run all code quality checks in sequence.

Execute the following skills in order:
1. `/format` - Format the code
2. `/lint` - Lint with auto-fix
3. `/typecheck` - Type check
4. `/test` - Run tests and check test coverage > 80%

Stop at the first failure and report the issue.
