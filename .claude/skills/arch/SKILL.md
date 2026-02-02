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

1. **Only `main.py` is allowed at project root** - all other Python source files must be in subfolders
2. **Test files should be alongside their source** or in a dedicated `tests/` folder
3. **Allowed root items**: `main.py`, `pyproject.toml`, `README.md`, `CLAUDE.md`, `.env`, `.gitignore`, config files (`.python-version`, `uv.lock`), and folders

## Check Process

1. List all `.py` files at project root (not in subfolders)
2. For each file found:
   - `main.py` is allowed
   - Any other `.py` file is a violation

3. Report violations with suggested target folders:
   - `config.py` → `config/` or `core/`
   - `models.py` → `models/` or `domain/`
   - `enums.py` → `models/` or `domain/`
   - `exceptions.py` → `core/` or `exceptions/`
   - `logger.py` → `core/` or `logging/`
   - `utils.py` → `utils/`
   - `*_test.py` → alongside source file or `tests/`

4. If violations found, fail with a clear list of files that need to be moved
