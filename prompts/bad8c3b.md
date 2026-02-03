# Commit bad8c3b - AI Readiness Setup Session

## Context

The user wanted to set up the project to be "AI ready" for collaboration with AI coding assistants. They had already created a CLAUDE.md file with project conventions and shared Python project guidelines.

---

## Conversation Flow

### User Prompt 1

> "I need, using the project guidelines setup all the project so it's completely AI ready (we can work with AI on the project). I already have a CLAUDE.MD (you can check it if you think there is something critical to change but otherwise let's concentrate on other things). Please propose me a list of skills and hooks according to the guidelines. For now we are planning, don't write anything and don't write the code for skills and hooks, only list them for now so we can discuss it"

The user provided their Python Project Guidelines document covering:
- Core principles (type everything, single responsibility, no over-engineering)
- Project setup requirements (linter, formatter, type checker, test runner, pre-commit hooks)
- AI readiness goals
- Code organization (layered architecture, mappers, services)
- Error handling, logging, testing conventions

### Assistant Response 1

Analyzed the current project state:
- Uses `uv` as package manager with lockfile ✓
- Has `ruff` for linting/formatting ✓
- Pylance in VSCode with strict type checking ✓
- Missing: CLI type checker, test runner, Claude configuration

Proposed initial list:

**Skills (Commands):**
- `/lint`, `/format`, `/typecheck`, `/test`, `/check`

**Skills (AI-powered):**
- `/review` - code review against guidelines

**Hooks:**
- PostToolUse (Edit/Write): auto-format
- PreToolUse (git commit): run checks
- Stop: session summary

**Missing dependencies:** pyright, pytest, pytest-asyncio

### User Prompt 2

> "j'ai aussi vu ce plugin https://github.com/anthropics/claude-plugins-official/blob/main/plugins/code-simplifier/agents/code-simplifier.md la commande review doit aussi faire une critique du code je pense (pour faire vraiment une review). Mais du coup on n'utilise pas de skills ici, que pourrait-on ajouter en skills?"

User pointed out:
1. They saw a code-simplifier plugin and wanted `/review` to include actual code critique
2. The proposed items were mostly CLI commands, not real AI-powered skills

### Assistant Response 2

Clarified the distinction:
- **Skills** = AI reasoning (review, simplify, test-gen, explain, refactor)
- **Hooks** = automation of CLI commands

Proposed AI-powered skills:
- `/review` - complete review with qualitative critique
- `/simplify` - simplify code (inspired by the plugin)
- `/test-gen` - generate tests following conventions
- `/explain` - explain code sections
- `/refactor` - refactor following project patterns

### User Prompt 3

> "explain et refactor je ne suis pas sûr. j'aimais bien les commandes quand même, je pense qu'il faut les deux. Dans les hooks il faut aussi ajouter l'usage de la simplification et de la review"

User decided:
- Remove `/explain` and `/refactor` (not sure about them)
- Keep both command skills AND AI skills
- Add simplify and review to hooks (automation)

### Assistant Response 3

Updated proposal with hooks for:
- Auto-format (PostToolUse)
- Pre-commit (lint + typecheck + review AI)
- Simplify suggestion (session end)
- Session summary (Stop)

### User Prompt 4

Asked three questions:
1. Simplify hook: on every edit or on demand?
2. Pre-commit review: blocking or informative?
3. Include pytest in pre-commit?

### User Response 4

> "1. je pense qu'il s'execute sur demande + avant la fin de la session une dernière fois. 2. bloquant 3. le pre commit hook doit tout faire du linter jusqu'aux tests"

Decisions:
1. Simplify: on demand + once before session end (not on every edit)
2. Pre-commit: blocking
3. Pre-commit must run everything: lint → typecheck → tests

### User Prompt 5

> "une autre IA a proposé les modifs suivantes, qu'en penses-tu?"

User shared feedback from another AI suggesting:
- Add `--fix` to `/check` command
- Remove `--fix` from PostToolUse (keep only format)
- Move pytest to pre-push instead of pre-commit
- Make session-end simplify a report/suggestion, not automatic
- Add hook for sensitive files

### Assistant Response 5

Evaluated each suggestion:

**Accepted:**
- `--fix` in `/check` - logical to auto-fix what can be fixed
- Session-end as report only - safer, avoids regression risk

**Partially accepted:**
- Remove `--fix` from PostToolUse - reasonable caution

**Rejected:**
- pytest in pre-push - user explicitly wanted everything in pre-commit
- Sensitive files hook - over-engineering for this project
- Quick vs complete review distinction - unnecessary complexity

### User Prompt 6

> "oui je préfère le garder"

Confirmed: keep pytest in pre-commit hook.

### User Prompt 7

> "pourquoi le /check ne fait pas le /format ?"

Pointed out inconsistency: `/check` should include formatting.

### Assistant Response 7

Fixed: `/check` now runs format → lint → typecheck → test in order.

### User Prompt 8

> "est-ce qu'une commande peut appeler d'autres commandes ? plus simple dans ce cas"

Asked if a skill can call other skills for maintainability.

### Assistant Response 8

Yes, `/check` can call `/format` → `/lint` → `/typecheck` → `/test` instead of duplicating commands. More maintainable.

### User Prompt 9

> "ok parfait let's go pour l'implem"

Green light to implement.

---

## Implementation Details

### Dependencies Added

```bash
uv add --dev pyright pytest pytest-asyncio
```

Result in pyproject.toml:
```toml
[dependency-groups]
dev = [
    "pyright>=1.1.408",
    "pytest>=9.0.2",
    "pytest-asyncio>=1.3.0",
    "ruff>=0.9.6",
]
```

### Directory Structure Created

```
.claude/
├── settings.json
├── hooks/
│   ├── format.sh
│   └── pre-commit.sh
└── skills/
    ├── check/SKILL.md
    ├── format/SKILL.md
    ├── lint/SKILL.md
    ├── review/SKILL.md
    ├── simplify/SKILL.md
    ├── test-gen/SKILL.md
    ├── test/SKILL.md
    └── typecheck/SKILL.md
```

### Skills Implementation

#### Command Skills

**`/lint`** - Runs `uv run ruff check --fix .`

**`/format`** - Runs `uv run ruff format .`

**`/typecheck`** - Runs `uv run pyright .`

**`/test`** - Runs `uv run pytest`

**`/check`** - Calls `/format` → `/lint` → `/typecheck` → `/test` in sequence, stops at first failure

#### AI Skills

**`/review`**
1. Runs `/check` first
2. If checks pass, performs qualitative review against CLAUDE.md:
   - Checks for red flags (print(), generic exceptions, missing types, vague names, etc.)
   - Validates architecture (services, data layer, mappers)
   - Outputs structured report with file:line references

**`/simplify`**
- Analyzes code for complexity reduction opportunities
- Looks for: deep nesting, redundancy, unclear naming, missing types
- Outputs suggestions with priority ranking
- Does NOT auto-apply changes (human review required)

**`/test-gen`**
- Generates tests following project conventions
- AAA pattern, factories, parameterized tests
- Places test files next to source files
- Mocks external calls

### Hooks Implementation

**settings.json:**
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format.sh",
            "timeout": 30
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-commit.sh",
            "timeout": 120
          },
          {
            "type": "prompt",
            "prompt": "If this is a git commit command, quickly review the staged changes against CLAUDE.md guidelines...",
            "timeout": 60
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Before ending, check if there are uncommitted changes to Python files. If so, briefly list the modified files and suggest running /simplify on them...",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**format.sh:**
- Triggered after Edit/Write on Python files
- Runs `ruff format` on the modified file only

**pre-commit.sh:**
- Triggered before any Bash command
- Only intercepts `git commit` commands
- Runs: format check → lint → typecheck → pytest
- Blocks commit with specific error message if any step fails
- After CLI checks pass, AI prompt reviews against CLAUDE.md

### Other Changes

- `.gitignore`: Added `.claude/settings.local.json` for personal overrides

---

## Final Configuration Summary

| Component | Details |
|-----------|---------|
| **Command Skills** | `/lint`, `/format`, `/typecheck`, `/test`, `/check` |
| **AI Skills** | `/review`, `/simplify`, `/test-gen` |
| **Auto-format Hook** | PostToolUse on Edit/Write → `ruff format` |
| **Pre-commit Hook** | Blocking: format + lint + typecheck + pytest + AI review |
| **Session Summary Hook** | Suggests `/simplify` on modified files |
| **Dev Dependencies** | pyright, pytest, pytest-asyncio, ruff |
