---
name: check
description: Run all checks (format, lint, typecheck, test, arch) on the codebase
user-invocable: true
allowed-tools:
  - Bash
  - Skill
  - Glob
  - Read
---

# Check

Run all code quality checks in sequence.

Execute the following skills in order:
1. `/arch` - Check project architecture (files properly organized)
2. `/format` - Format the code
3. `/lint` - Lint with auto-fix
4. `/typecheck` - Type check
5. `/test` - Run tests and check test coverage > 80%

Stop at the first failure and report the issue.
