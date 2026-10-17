import json
import re


def parse_json(text: str) -> dict:
    if not isinstance(text, str):
        raise ValueError("Expected JSON text")
    # Never expose model reasoning markup as an operator answer.
    cleaned = re.sub(r"<think(?:ing)?>.*?</think(?:ing)?>", "", text, flags=re.I | re.S).strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON output") from exc
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value
