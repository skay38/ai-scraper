# Commit ff4a4eb - Add Architecture Check Skill

## Problem

The project had Python files scattered at the root level instead of organized in proper folders:
- `config.py`, `models.py`, `enums.py`, `exceptions.py`, `logger.py`, `utils.py` at root
- Test files (`*_test.py`) also at root level

This violates the layered architecture pattern described in CLAUDE.md.

## Solution

Created a new `/arch` skill that validates project structure:

1. **New skill**: `.claude/skills/arch/SKILL.md`
   - Checks that only `main.py` exists at project root
   - Reports violations with suggested target folders
   - Provides clear guidance on where files should be moved

2. **Updated `/check` skill**: Added `/arch` as the first check in the sequence
   - Architecture validation runs before format, lint, typecheck, and test
   - Ensures structure issues are caught early

## Architecture Rules

- Only `main.py` allowed at root
- All other Python files must be in subfolders
- Suggested folder mappings:
  - `config.py` → `config/` or `core/`
  - `models.py`, `enums.py` → `models/` or `domain/`
  - `exceptions.py`, `logger.py` → `core/`
  - `utils.py` → `utils/`
  - `*_test.py` → alongside source or `tests/`
