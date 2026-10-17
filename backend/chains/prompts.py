from pathlib import Path
import json
import yaml

ROOT = Path(__file__).resolve().parents[1] / "prompts"


def _config(name: str):
    if name not in {"planner", "maker", "summary", "repair", "greeting", "suggestions"}:
        raise ValueError("Unknown prompt")
    config = yaml.safe_load((ROOT / (name + ".yaml")).read_text())
    if not isinstance(config, dict) or set(config) != {"input", "prompt"}:
        raise ValueError("Prompt config requires input and prompt")
    fields = config["input"]
    if not isinstance(fields, dict) or set(fields) != {"required", "optional"}:
        raise ValueError("Prompt input requires explicit required and optional lists")
    for values in fields.values():
        if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values):
            raise ValueError("Prompt input names must be string lists")
    names = fields["required"] + fields["optional"]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate prompt input names")
    if not isinstance(config["prompt"], str):
        raise ValueError("Prompt reference must be a string")
    source = (ROOT / config["prompt"]).resolve()
    if source.parent != ROOT.resolve() or source.suffix != ".md":
        raise ValueError("Unsafe prompt reference")
    return config, source


def load_prompt(name: str) -> str:
    _, source = _config(name)
    return source.read_text() if name == "suggestions" else (ROOT / "persona.md").read_text() + "\n\n" + source.read_text()


def bind_prompt(name: str, payload: dict) -> str:
    """Validate labeled JSON inputs; Markdown is prose, never a format template."""
    config, _ = _config(name)
    fields = config["input"]
    if not isinstance(payload, dict):
        raise ValueError("Prompt payload must be a JSON object, not encoded text")
    missing = set(fields["required"]) - payload.keys()
    unknown = payload.keys() - set(fields["required"] + fields["optional"])
    if missing or unknown:
        raise ValueError(f"{name} prompt input mismatch: missing={sorted(missing)}, unknown={sorted(unknown)}")
    # Reject unsupported objects and non-finite numbers before any API call.
    json.dumps(payload, ensure_ascii=False, allow_nan=False)
    return load_prompt(name)
