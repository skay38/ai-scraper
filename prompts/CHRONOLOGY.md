# Decision Chronology

## 1. eb6a327 - CLAUDE.md Setup

**Goal:** Create AI-readable project conventions

**Decisions:**
- Include code conventions, architecture patterns, style preferences
- Exclude generic setup instructions (linters, pre-commit) - human-focused
- Add "Project Context" section explaining what the scraper does

---

## 2. bad8c3b - AI Readiness Setup

**Goal:** Make project fully AI-ready with skills and hooks

**Decisions:**
- Skills split into **commands** (`/lint`, `/format`, `/typecheck`, `/test`, `/check`) and **AI-powered** (`/review`, `/simplify`, `/test-gen`)
- Removed `/explain` and `/refactor` - not convinced they're needed
- Pre-commit hook must be **blocking** and run **everything** (format → lint → typecheck → tests)
- `/simplify` runs on demand + once before session end (not on every edit)
- Session-end `/simplify` is a **report only**, not automatic changes
- Keep pytest in pre-commit (rejected suggestion to move to pre-push)
- `/check` calls other skills in sequence for maintainability

---

## 3. ba7d05c - Git Pre-commit Hook

**Goal:** Ensure pre-commit runs for all contributors, not just Claude Code

**Decisions:**
- Use `.githooks/` directory + `core.hooksPath` configuration (not `pre-commit` framework)
- Contributors run `git config core.hooksPath .githooks` once after cloning

---

## 4. bb7b71a - Enhanced Stop Hook

**Goal:** Add hooks for review, simplify, test-gen skills

**Decisions:**
- All suggestions happen at session end via Stop hook (not on every edit)
- `/test-gen` suggested for **any** Python source file modified (not just when test files untouched)

---

## 5. 5931c52 - Fix Pre-commit Hook

**Goal:** Fix hook running on all bash commands

**Decisions:**
- Remove redundant prompt hook (bash script already handles validation)
- Make bash script silently exit on non-git commands

---

## 6. 7a3c805 - Enhanced Hooks

**Goal:** Better align hooks with Python guidelines

**Decisions:**
- Merge format + lint into single `lint-format.sh`
- Add `check-quality.sh` for guideline violations (print, generic exceptions, missing types)
- Change Stop hook from prompt-based to **agent-based** (can actually read files)
- Declined SessionStart context hook

---

## 7. 15429dc - Align Codebase with Guidelines

**Goal:** Fix all CLAUDE.md violations in code

**Decisions:**
- Replace all `print()` with structured logger
- Create custom exception hierarchy (no generic `Exception`)
- Create `PricingStatus` and `BusinessType` enums (no magic strings)
- Create typed Pydantic models (no raw dict returns)

---

## 8. c76bc13 - Code Review and Tests

**Goal:** Run `/review` and fix issues

**Decisions:**
- Create comprehensive test suite (P0 priority - was 0% coverage)
- Add `JsonParseError` to exception handling
- Move hardcoded `"res.json"` to config constant

---

## 9. ae2078c - Extract BatchScraperService

**Goal:** Simplify main.py

**Decisions:**
- Extract batch scraping logic into dedicated service
- Update `/test` skill to report coverage and files without tests
- Fix Stop hook to not trigger when tests already run

---

## 10. ff4a4eb - Add /arch Skill

**Goal:** Validate project structure

**Decisions:**
- Create `/arch` skill to check file organization
- Only `main.py` allowed at root level
- Run `/arch` as first check in `/check` sequence

---

## 11. 4048b3d - Project Reorganization

**Goal:** Fix architecture violations

**Decisions:**
- Core utilities (config, logger, exceptions) go in `utils/` (not `core/`)
- Test files placed **beside** source files (not in separate `tests/` folder)
- Allow common root items: `.env`, `.githooks/`, `res.json`, etc.

---

## 12. d0ed77b - LLM Prompts Skill

**Goal:** Add skill for checking LLM prompts

**Decisions:**
- Create `/llm-prompts` skill for prompt best practices
- Add `/simplify` and `/llm-prompts` to `/review` workflow
- Extract inline prompts to `llm_prompts/` module with typed builders

---

## 13. 28f64db - src/ Layout and Layered Architecture Refactoring

**Goal:** Reorganize project structure and apply layered architecture with proper separation of concerns

**Structure Decisions:**
- Move all Python folders into `src/` directory
- Create `clients/` folder for pure API clients
- Create `mappers/` folder for pure transformation functions
- Create `services/` for business logic orchestration
- Test files remain **colocated** with source files in `src/`

**Code Architecture Decisions:**
- Separate AnthropicClient into:
  - **Pure API client** (`send_message()` only - returns str or raises exception)
  - **ExtractionService** (orchestrates extraction using mappers)
- Use **exception-based** error handling (return data directly, raise on failure)
- Extract transformations into **pure mapper functions**:
  - `clean_html()` - remove scripts/styles from HTML
  - `normalize_pricing_urls()` - resolve relative URLs
  - `parse_company_response()` - parse LLM JSON response

**Simplification Decisions:**
- Remove 5 unused exception classes (ConnectionTimeoutError, ReadTimeoutError, NetworkError, TooManyRedirectsError, DataExtractionError)
- Add `PricingStatus.empty_statuses()` classmethod to eliminate duplicate status lists in scraper.py and batch_scraper.py
- Fix `company_description` default (was incorrectly using BusinessType.UNKNOWN)
