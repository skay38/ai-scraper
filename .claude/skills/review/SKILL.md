---
name: review
description: Complete code review with linting, type checking, tests, and qualitative analysis against project guidelines
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Skill
---

# Review

Perform a complete code review on the project or specified files.

## Steps

1. **Run automated checks** by invoking `/check` (format, lint, typecheck, test)

2. **Run simplify analysis** by invoking `/simplify` to identify complexity and redundancy issues

3. **Check LLM prompts** by invoking `/llm-prompts` if the codebase contains LLM integrations

4. **If checks pass**, perform qualitative review against CLAUDE.md guidelines:

### Check for Red Flags
- `print()` statements in production code
- Generic exceptions (`Exception`, `ValueError`) in business logic
- Functions without type annotations
- Raw `dict` instead of typed models for structured data
- Vague function names (`handle_data`, `process_stuff`, `run_logic`)
- Positional arguments for 3+ parameters
- String literals that should be enums
- `**kwargs` in business logic
- Magic strings/numbers
- Naive datetimes
- Commented-out code
- Deep nesting instead of guard clauses

### Check Architecture
- Services contain business logic only
- Data layer has no business rules
- Mappers are pure functions
- Guard clauses used over deep nesting

### Check Code Quality
- Clear, descriptive naming
- Single responsibility per function/module
- No over-engineering or premature abstractions
- Proper error handling with custom exceptions
- Structured logging (no f-strings in log messages)

## Output

Provide a structured report:
1. **Automated Checks**: Pass/Fail summary
2. **Red Flags Found**: List with file:line references
3. **Architecture Issues**: Any violations of layered architecture
4. **Suggestions**: Concrete improvements ranked by priority
