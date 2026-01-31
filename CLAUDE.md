# Python Project Conventions

## Project Context

This is an AI-powered web scraper that extracts structured company information (name, description, business type, pricing) from website URLs. The scraper fetches HTML content, sends it to an LLM for data extraction, and outputs structured JSON results.

## Core Principles

- **Type everything**: No function without type annotations
- **Follow existing patterns**: Always check existing code before writing new code
- **Single responsibility**: One function/module = one job
- **Simple and readable**: Explicit, minimalistic, well-structured code
- **No over-engineering**: Don't abstract for single use cases, don't design for hypothetical futures

## Naming Conventions

- `snake_case` for functions and variables
- `PascalCase` for classes
- Names must precisely describe what the function/variable does
- Avoid vague names: `handle_data`, `process_stuff`, `run_logic`, `do_thing`
- Use consistent verb prefixes across the codebase

## Code Organization

### Layered Architecture

Separate business logic from data access and transformation:

- **Service**: Contains all business logic, only layer that accesses the data layer
- **Data layer**: Data access only, no business rules
- **Mapper**: Pure data transformation functions (no side effects, no I/O)

### Mappers

- Use a mapper when transformation exceeds 2-3 lines
- Naming convention: `<source>_to_<target>()`
- Must be pure functions with single responsibility

### Services

- Use guard clauses over deep nesting
- Keep services short and focused
- Use mappers for verbose transformations
- Only services contain business logic

Example:
```python
async def activate(self, id: UUID) -> Item:
    item = await self.find_or_raise(id)

    if item.is_active:
        raise ConflictError("Already active")

    if not item.is_valid:
        raise ValidationError("Configuration is invalid")

    return await self.data.update(id, status=Status.ACTIVE)
```

## Type Safety

- All functions must have type annotations
- Use explicit generic types: `list[str]` not `list`, `dict[str, Any]` not `dict`
- Use typed models for all structured data (never raw `dict` for data contracts)
- Use enums for status fields and constant values
- Always use timezone-aware datetimes

```python
# Typed empty variables
items: list[str] = []  # Good
items = []             # Bad

# None handling
name = get_name() or "default"
```

## Error Handling

- Never use `Exception`, `ValueError` or other generic exceptions in business logic — define custom exceptions
- Exception messages must be static strings; pass dynamic data separately
- Always preserve the original exception when re-raising
- Only use try/except for: re-raising with context, specific recovery, or explicitly dropping errors in batch operations
- Never catch an exception just to log it

## Logging

- Never use `print()` — always use the logger
- Use static messages with dynamic data in structured fields

```python
# Good
logger.info("Processing item", extra={"item_id": item.id})

# Bad
logger.info(f"Processing item {item.id}")
```

- Don't log inside exception handlers (global handler already does it)
- Don't log sensitive data (passwords, tokens, PII)

## Code Style

- Code should be self-explanatory through clear naming and short functions
- Comments explain the "why", not the "what"
- Reduce unnecessary complexity and nesting
- Eliminate redundant code and abstractions
- Clarity over brevity
- Avoid nested ternaries

## Red Flags to Avoid

- `print()` in production code
- Generic exceptions in business logic
- Functions without type annotations
- Raw `dict` instead of typed models for structured data
- Vague function names
- Positional arguments for 3+ parameters (use keyword arguments)
- String literals that should be enums
- `*kwargs` in business logic
- Magic strings/magic numbers
- Naive datetimes
- Commented-out code
- Deep nesting instead of guard clauses
- Catching exceptions just to log them
