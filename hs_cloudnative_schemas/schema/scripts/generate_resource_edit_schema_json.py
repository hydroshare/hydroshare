"""Generate the JSON schema for the CoreMetadataEdit model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hs_cloudnative_schemas.schema.core import CoreMetadataEdit


SCHEMA_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = SCHEMA_DIR / "json_schemas"
OUTPUT_FILE = OUTPUT_DIR / "resource_edit_schema.json"
SKIP_VALUE = object()


def _normalize_schema_value(value: Any, key: str | None = None) -> Any:
    """Normalize schema values so they can be written as stable JSON."""
    if isinstance(value, str):
        return value.replace("$defs", "definitions")

    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for item_key, item_value in value.items():
            normalized_key = "definitions" if item_key == "$defs" else item_key
            normalized_value = _normalize_schema_value(item_value, key=item_key)
            if normalized_value is not SKIP_VALUE:
                normalized[normalized_key] = normalized_value
        return normalized

    if isinstance(value, list):
        return [item for item in (_normalize_schema_value(item) for item in value) if item is not SKIP_VALUE]

    if isinstance(value, tuple):
        return [item for item in (_normalize_schema_value(item) for item in value) if item is not SKIP_VALUE]

    try:
        json.dumps(value)
    except TypeError:
        if key == "default":
            return SKIP_VALUE
        return str(value)

    return value


def convert_defs_to_definitions(schema: dict[str, Any]) -> dict[str, Any]:
    """Convert Pydantic v2 `$defs` keys to `definitions` for compatibility."""
    return _normalize_schema_value(schema)


def build_resource_edit_schema() -> dict[str, Any]:
    """Build the JSON schema for the CoreMetadataEdit model."""
    schema = CoreMetadataEdit.model_json_schema()
    return convert_defs_to_definitions(schema)


def write_resource_edit_schema(output_path: Path = OUTPUT_FILE) -> Path:
    """Write the generated schema to disk and return the output path."""
    schema = build_resource_edit_schema()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def main() -> None:
    """Generate the CoreMetadataEdit schema artifact."""
    write_resource_edit_schema()


if __name__ == "__main__":
    main()
