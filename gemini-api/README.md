# Gemini Adapter

A lightweight wrapper around `google-genai` for:
- text generation
- token counting
- prompt validation before sending requests

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from gemini_adapter import GeminiAdapter

adapter = GeminiAdapter(
    api_key="YOUR_GEMINI_API_KEY",
    model_name="gemini-2.5-flash",
)

result = adapter.generate(
    prompt="Explain adapters in Python in simple words.",
    system_instruction="You are a concise coding mentor.",
)

if result["success"]:
    print(result["text"])
else:
    print(result["error_code"], result["error"])
```

## API

### `generate(prompt, system_instruction=None)`
Returns:

```python
{
  "success": True,
  "text": "...",
  "model": "gemini-2.5-flash",
  "tokens_used": 123
}
```

or on failure:

```python
{
  "success": False,
  "error": "...",
  "error_code": "INVALID_API_KEY"
}
```

### `generate_with_context(user_input, context=None, system_instruction=None)`
`context` format:

```python
[
  {"role": "user", "text": "Hi"},
  {"role": "assistant", "text": "Hello!"},
]
```

Example:

```python
result = adapter.generate_with_context(
    user_input="Continue from our previous discussion.",
    context=[
        {"role": "user", "text": "What is dependency injection?"},
        {"role": "assistant", "text": "It is a way to provide dependencies from outside."},
    ],
)
```

### `count_tokens(text)`
Counts tokens using Gemini API. If the API call fails, it falls back to rough estimation (`len(text) // 4`).

### `validate_prompt(system_prompt=None, user_input="", context="")`
Checks whether input is likely to fit in model token budget.
- Uses `max_tokens` set on adapter.
- Applies a 20% safety buffer.

Returns:
- `(True, None)` if valid
- `(False, "...")` if likely to exceed limit or when validation fails

## Error Codes

- `INVALID_API_KEY`
- `RATE_LIMIT`
- `TOKEN_LIMIT_EXCEEDED`
- `API_ERROR`

## Notes

- This adapter is synchronous; do not use `await` with its methods.
- Keep your API key in environment variables or secret manager.
- Default model: `gemini-2.5-flash`.
