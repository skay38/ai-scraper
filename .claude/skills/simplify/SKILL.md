---
name: simplify
description: Analyze and simplify code by reducing complexity, eliminating redundancy, and improving readability
user-invocable: true
allowed-tools:
  - Read
  - Edit
  - Grep
  - Glob
---

# Simplify

Analyze the selected code or specified files and suggest simplifications.

## Analysis Criteria

Based on CLAUDE.md guidelines, look for:

### Complexity Reduction
- Deep nesting that can use guard clauses
- Complex conditionals that can be simplified
- Nested ternaries
- Long functions that should be split

### Redundancy Elimination
- Duplicate code patterns
- Unnecessary abstractions for single use cases
- Over-engineered solutions
- Unused imports, variables, or functions

### Readability Improvements
- Vague names that need clarification
- Missing type annotations
- Complex expressions that need decomposition
- Magic numbers/strings that need constants or enums

## Output

For each issue found:
1. **Location**: file:line reference
2. **Issue**: What's wrong
3. **Suggestion**: Concrete fix with code example
4. **Priority**: High/Medium/Low based on impact

If `$ARGUMENTS` contains a file path, focus on that file.
Otherwise, analyze recently modified files or the entire codebase.

**Important**: Present suggestions for human review. Do not auto-apply changes without confirmation.
