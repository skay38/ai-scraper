# Technical test: AI Scraper

## 🎯 Objective

You need to develop a Python scraper that extracts information about companies from a list of 1000 URLs.

## 📌 Constraints & Expectations

⏳ Duration: 1 hour

### 📤 Input

A list of 1000 URLs containing company pages.

Example URLs:

```plain
https://exemple-entreprise.com
https://startup-cool.io
```

### 📥 Expected Output

For each successfully processed URL, your script should return a structured JSON containing:

```json
{
  "url": "https://example-company.com",
  "success": true,
  "data": {
    "company_name": "Example Company",
    "company_description": "A company specializing in AI solutions...",
    "business_type": "B2B",
    "pricing": "$2000 per user per month"
  }
}
```

Or

```json
{
  "url": "https://example-company.com",
  "success": false,
  "error": "description of the error"
}
```

### 📚 Libraries

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [HTTPX](https://www.python-httpx.org/) or [Requests](https://requests.readthedocs.io/en/latest/)
- [Pydantic](https://docs.pydantic.dev/)
- [OpenAI SDK](https://github.com/openai/openai-python)

## 🔍 Steps to Follow

### 1️⃣ Step 1 - Scrape Web Pages

Use **requests or httpx** to fetch the HTML content of the pages. You should not use a third party service to fetch the content of the pages.

**Handle as many errors as possible** to maximize the number of successfully processed URLs.

### 2️⃣ Step 2 - Extract Information Using an LLM

Once the text is extracted, send it to a LLM (GPT-4o Mini) to structure the data.

Model name: `gpt-4.1-mini`

API Key: ask for it

**Note:** This model has a rate limit of 3000 requests per minute (RPM) but is shared with other resources.

📄 **Documentation:**  [https://platform.openai.com/docs/guides/structured-outputs](https://platform.openai.com/docs/guides/structured-outputs)

### 3️⃣ Step 3 - Evaluate Data Quality

If you have additional time, assess the quality of extracted information by implementing validation checks.

## ✅ Evaluation Criteria

| **Criterion** | **Expectations** |
| --- | --- |
| **Number of URLs processed** | Maximizing scraping despite potential errors |
| **Code Quality** | Clear and well-structured code |
| **Data quality** | Ensuring data relevance and accuracy |
| **AI** | Well-designed prompt |
| **Evaluation** | Ability to track evolution of the quality of the data |

Good luck ! 🚀

---

## Development Setup

After cloning, activate the pre-commit hooks:

```bash
git config core.hooksPath .githooks
```

This runs format, lint, typecheck, and tests before each commit.
