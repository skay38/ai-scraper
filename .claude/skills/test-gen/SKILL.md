---
name: test-gen
description: Generate tests for a function or module following project testing conventions
user-invocable: true
argument-hint: "[file-path or function-name]"
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
---

# Test Generation

Generate tests for the specified function, class, or module.

## Conventions (from CLAUDE.md)

- Test files placed next to the code being tested (e.g., `foo.py` → `foo_test.py`)
- AAA pattern: Arrange / Act / Assert
- Test behavior, not implementation (public interfaces only)
- Use factories for test data generation
- Mock external network calls
- Control time in time-dependent tests
- Parameterize tests for multiple cases
- Don't test private methods
- Don't depend on test execution order
- Don't depend on data ordering without explicit sorting

## Steps

1. Read the target file/function specified in `$ARGUMENTS`
2. Identify public interfaces to test
3. Determine edge cases and error scenarios
4. Generate test file with:
   - Proper imports
   - Test class or functions following naming convention
   - Fixtures if needed
   - Parameterized tests for multiple scenarios

## Output

Create a test file next to the source file with comprehensive tests.
Report what was generated and any assumptions made.
