---
name: arch
description: Check project architecture - ensure files are properly organized in folders
user-invocable: true
allowed-tools:
  - Bash
  - Glob
  - Read
---

# Architecture Check

Verify that the project follows proper folder organization.

## Rules

1. **Only `main.py` and `conftest.py` are allowed at project root** - all other Python source files must be in subfolders
2. **Test files should be alongside their source** or in a dedicated `tests/` folder

### Allowed Root Items

**Files:**
- `main.py`, `conftest.py` (Python entry points)
- `pyproject.toml`, `uv.lock`, `.python-version` (project config)
- `README.md`, `CLAUDE.md`, `.gitignore` (documentation)
- `.env`, `.env.example`, `.env.local` (environment files)
- `res.json`, `output.json` (output files - consider gitignoring)

**Directories:**
- `.git`, `.github`, `.githooks` (git-related)
- `.vscode`, `.idea` (IDE config)
- `.venv`, `venv`, `.env` (virtual environments)
- `__pycache__`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache` (caches)
- `htmlcov`, `.coverage` (coverage reports)
- `.claude` (Claude Code config)
- Any folder listed in `ALLOWED_TOP_LEVEL` below

## Expected Module Structure

```
project/
├── main.py              # Entry point (allowed at root)
├── conftest.py          # Pytest config (allowed at root)
├── models/              # Data models and enums
│   ├── __init__.py
│   ├── schemas.py       # Pydantic models
│   └── enums.py
├── services/            # Business logic
│   └── ...
├── llm_prompts/         # LLM prompt constants and builders
│   ├── __init__.py
│   └── extraction.py
├── utils/               # Core utilities (config, logger, exceptions, helpers)
│   ├── __init__.py
│   ├── config.py
│   ├── logger.py
│   ├── exceptions.py
│   └── helpers.py
└── tests/               # Test files (or alongside source)
    └── ...
```

## Check Process

1. List all `.py` files at project root (not in subfolders)
2. For each file found:
   - `main.py` and `conftest.py` are allowed
   - Any other `.py` file is a violation

3. Report violations with suggested target folders:
   - `config.py` → `utils/`
   - `logger.py` → `utils/`
   - `exceptions.py` → `utils/`
   - `utils.py` → `utils/helpers.py`
   - `models.py` → `models/schemas.py`
   - `enums.py` → `models/`
   - `*_test.py` → `tests/` or alongside source file

4. If violations found, fail with a clear list of files that need to be moved
