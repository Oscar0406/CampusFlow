import json
import re


def extract_json(text: str) -> dict | list | None:
    """Extract first valid JSON object/array from raw LLM text."""
    if not text:
        return None
    text = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for opener, closer in [('{', '}'), ('[', ']')]:
        start = text.find(opener)
        end = text.rfind(closer) + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                continue
    return None
