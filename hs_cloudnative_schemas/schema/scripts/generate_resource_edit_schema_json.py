"""Generate the JSON schema for the CoreMetadataEdit model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic_core import CoreSchema
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue

from hs_cloudnative_schemas.schema.core import CoreMetadataEdit



class _GenerateJsonSchemaNoNullableAnyOf(GenerateJsonSchema):
    """A GenerateJsonSchema subclass that unwraps Optional[X] nullable schemas.
    """

    def nullable_schema(self, schema: CoreSchema) -> JsonSchemaValue:
        """Override the nullable_schema method to unwrap Optional[X] schemas.

        Pydantic expands ``Optional[X]`` into ``anyOf: [{...X...}, {type: null}]``.
        This method ensures that the inner schema is returned without adding an unnecessary
        null type and anyOf, preserving the intended schema structure.
        """
        return self.generate_inner(schema["schema"])

    def default_schema(self, schema: CoreSchema) -> JsonSchemaValue:
        """Override the default_schema method to handle None defaults.

        Pydantic expands ``Optional[X]`` into ``anyOf: [{...X...}, {type: null}]``.
        This method ensures that if the default is None, the inner schema is returned
        without adding an unnecessary null type and anyOf, preserving the intended schema structure.
        """
        if schema.get("default") is None:
            return self.generate_inner(schema["schema"])
        return super().default_schema(schema)


SCHEMA_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = SCHEMA_DIR / "json_schemas"
OUTPUT_FILE = OUTPUT_DIR / "resource_edit_schema.json"
SKIP_VALUE = object()


def _normalize_schema_value(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for item_key, item_value in value.items():
            if item_key == "default" and item_value is None:
                continue
            normalized_key = "definitions" if item_key == "$defs" else item_key
            normalized_value = _normalize_schema_value(item_value, key=item_key)
            if normalized_value is not SKIP_VALUE:
                normalized[normalized_key] = normalized_value
        return normalized

    if isinstance(value, list):
        return [
            item for item in (_normalize_schema_value(item) for item in value)
            if item is not SKIP_VALUE
        ]

    if isinstance(value, tuple):
        return [
            item for item in (_normalize_schema_value(item) for item in value)
            if item is not SKIP_VALUE
        ]

    if isinstance(value, str):
        if key == "$ref":
            return value.replace("#/$defs/", "#/definitions/")
        return value

    try:
        json.dumps(value)
    except TypeError:
        if key == "default":
            return SKIP_VALUE
        return str(value)

    return value


def convert_defs_to_definitions(schema: dict[str, Any]) -> dict[str, Any]:
    """Convert Pydantic `$defs` keys to `definitions` for compatibility."""
    return _normalize_schema_value(schema)


def build_resource_edit_schema() -> dict[str, Any]:
    """Build the JSON schema for the CoreMetadataEdit model."""
    schema = CoreMetadataEdit.model_json_schema(schema_generator=_GenerateJsonSchemaNoNullableAnyOf)
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
