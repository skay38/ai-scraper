---
name: llm-prompts
description: Check LLM prompts for best practices - separation of concerns, structured data injection, and proper typing
user-invocable: true
allowed-tools:
  - Read
  - Grep
  - Glob
---

# LLM Prompts Check

Analyze LLM prompts in the codebase for adherence to best practices.

## Guidelines

Based on CLAUDE.md, LLM prompts should follow these rules:

### 1. Separate Instructions from Dynamic Data
- Instructions should be static/constant text
- Dynamic data should be clearly injected, not concatenated inline
- Use clear delimiters or markers for dynamic sections

### 2. Use Structured Formats for Complex Data
- Prefer XML or JSON to inject complex data into prompts
- Avoid unstructured string concatenation
- Data should be clearly delineated from prompt text

### 3. Avoid String Concatenation
- Never build prompts with `+` or f-strings mixing instructions and data
- Use template placeholders or structured injection
- Keep prompt templates clean and readable

### 4. Extract Large Prompts into Constants
- Prompts longer than 3-5 lines should be constants
- Store prompts at module level or in dedicated prompt files
- Name constants descriptively: `EXTRACTION_PROMPT`, `SYSTEM_INSTRUCTION`

### 5. Type Prompt Builder Functions
- Functions that build prompts must have type annotations
- Return type should be explicit (`str`, or a typed prompt object)
- Parameters should be typed to prevent invalid data injection

## Check Process

1. Find all files that may contain LLM prompts:
   - Search for imports: `anthropic`, `openai`, `langchain`, `llm`
   - Search for common patterns: `prompt`, `system_message`, `user_message`
   - Check files in `services/`, `prompts/` directories

2. For each prompt found, check:
   - Is dynamic data clearly separated from instructions?
   - Are large prompts extracted to constants?
   - Is structured format (XML/JSON) used for complex data?
   - Are prompt builder functions properly typed?

## Output

For each issue found:
1. **Location**: file:line reference
2. **Issue**: What rule is violated
3. **Current**: Show the problematic code
4. **Suggestion**: How to fix it with code example

If `$ARGUMENTS` contains a file path, focus on that file.
Otherwise, scan the entire codebase for LLM prompt usage.

## Examples

### Bad: String concatenation
```python
prompt = f"Extract data from this HTML: {html_content}"
```

### Good: Structured injection
```python
EXTRACTION_PROMPT = """Extract structured data from the provided HTML content.

<html_content>
{html_content}
</html_content>

Return JSON with: name, description, pricing.
"""

def build_extraction_prompt(html_content: str) -> str:
    return EXTRACTION_PROMPT.format(html_content=html_content)
```

### Bad: Inline prompt
```python
response = client.messages.create(
    messages=[{"role": "user", "content": f"Analyze {data} and return {format}"}]
)
```

### Good: Extracted constant with typed builder
```python
ANALYSIS_PROMPT = """Analyze the provided data and return results in the specified format.

<data>
{data}
</data>

<output_format>
{output_format}
</output_format>
"""

def build_analysis_prompt(data: str, output_format: str) -> str:
    return ANALYSIS_PROMPT.format(data=data, output_format=output_format)
```
