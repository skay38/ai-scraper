---
name: test
description: Run pytest on the codebase
user-invocable: true
allowed-tools:
  - Bash
---

# Test

Run pytest on the project with coverage and identify files without tests.

## Steps

1. Run pytest with coverage:
```bash
uv run pytest --cov=. --cov-report=term-missing -q
```

2. After running tests, analyze the coverage output and report:
   - Total test count and pass/fail status
   - Overall coverage percentage
   - List of project files with 0% coverage (excluding test files, `__init__.py`, and `main.py`)
   - For files with partial coverage, note the missing lines if significant

3. Format the summary as:
   - **Tests**: X passed / Y failed
   - **Coverage**: XX%
   - **Files without tests**: list any .py files at 0% coverage that should have tests
