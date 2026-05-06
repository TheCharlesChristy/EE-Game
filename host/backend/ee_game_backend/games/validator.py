"""JSON schema validation helpers for v1 protocol messages."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    import jsonschema
except Exception:  # pragma: no cover - fallback for minimal offline installs
    jsonschema = None


class SchemaValidationError(ValueError):
    pass


def validate_message(schema_name: str, message: dict[str, Any]) -> None:
    """Validate message against shared/schemas/v1/<schema_name>.schema.json."""
    schema = _load_schema(schema_name)
    if jsonschema is not None:
        try:
            jsonschema.validate(message, schema)
        except jsonschema.ValidationError as exc:
            raise SchemaValidationError(exc.message) from exc
        return
    _fallback_validate(schema, message)


@lru_cache(maxsize=16)
def _load_schema(schema_name: str) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[4]
    path = root / "shared" / "schemas" / "v1" / f"{schema_name}.schema.json"
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _fallback_validate(schema: dict[str, Any], message: dict[str, Any]) -> None:
    for field in schema.get("required", []):
        if field not in message:
            raise SchemaValidationError(f"Missing required field: {field}")
    props = schema.get("properties", {})
    for name, prop in props.items():
        if "const" in prop and message.get(name) != prop["const"]:
            raise SchemaValidationError(f"{name} must be {prop['const']!r}")
