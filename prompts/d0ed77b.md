# Commit d0ed77b - LLM Prompts Skill and Prompt Extraction

## Context

The user wanted to add a new skill for checking LLM prompts and increase the application of the `/simplify` skill.

---

## Conversation Flow

### User Prompt 1

> "Please add a new skill for checking llm prompts. Also I think that the simplify skill is not applied enough"

User provided LLM prompt guidelines from CLAUDE.md:
- Clearly separate instructions from dynamic data
- Use structured format (XML, JSON) to inject complex data
- Avoid string concatenation to build prompts
- Extract large prompts into constants
- Type prompt builder functions

### Assistant Response 1

Created `/llm-prompts` skill and integrated `/simplify` into:
1. The `/review` skill workflow (as step 2)
2. The Stop hook suggestions (for code with complexity)

### User Prompt 2

> "Please fix this" (referring to LLM Prompts Analysis output)

The `/llm-prompts` skill identified issues in `services/anthropic_client.py`:
- Inline company extraction prompt (22 lines) with f-string mixing
- Inline pricing extraction prompt with f-string mixing
- Prompts not in dedicated module

### Assistant Response 2

Fixed all issues by:
1. Creating `llm_prompts/` module with prompt constants
2. Adding typed builder functions
3. Refactoring `anthropic_client.py` to use the builders

---

## Implementation

### 1. Created `/llm-prompts` Skill

`.claude/skills/llm-prompts/SKILL.md`:
- Checks separation of instructions from dynamic data
- Verifies structured formats (XML/JSON) for complex data
- Flags string concatenation in prompts
- Ensures large prompts are extracted to constants
- Checks that prompt builder functions are typed

### 2. Updated `/review` Skill

Added two new steps:
1. Run `/simplify` analysis (step 2)
2. Check LLM prompts with `/llm-prompts` (step 3)

### 3. Updated Stop Hook

Added suggestions for:
- `/simplify <file>` - when code has deep nesting or complexity
- `/llm-prompts` - when LLM prompt code is modified

### 4. Created `llm_prompts/` Module

**llm_prompts/__init__.py** - exports builder functions

**llm_prompts/extraction.py**:
```python
COMPANY_EXTRACTION_PROMPT = """...<source_url>{url}</source_url>..."""
PRICING_EXTRACTION_PROMPT = """...<content>{content}</content>..."""

def build_company_extraction_prompt(url: str, content: str, max_chars: int) -> str
def build_pricing_extraction_prompt(content: str, max_chars: int) -> str
```

### 5. Refactored `anthropic_client.py`

Before (inline f-string prompt):
```python
prompt = f"""You are a data extraction assistant...
Content (first {HTML_TRUNCATE_MAIN} characters):
{truncated}
..."""
```

After (typed builder call):
```python
prompt = build_company_extraction_prompt(
    url=url, content=truncated, max_chars=HTML_TRUNCATE_MAIN
)
```

---

## Files Changed

| File | Change |
|------|--------|
| `.claude/skills/llm-prompts/SKILL.md` | Created - LLM prompt checking skill |
| `.claude/skills/review/SKILL.md` | Added /simplify and /llm-prompts steps |
| `.claude/settings.json` | Added /simplify and /llm-prompts to Stop hook |
| `.claude/skills/arch/SKILL.md` | Added llm_prompts/ to expected structure |
| `llm_prompts/__init__.py` | Created - module exports |
| `llm_prompts/extraction.py` | Created - prompt constants and builders |
| `services/anthropic_client.py` | Refactored to use prompt builders |

---

## Final State

All checks pass:
- Format
- Lint
- Type check (0 errors)
- Tests (28 anthropic_client tests passed)
