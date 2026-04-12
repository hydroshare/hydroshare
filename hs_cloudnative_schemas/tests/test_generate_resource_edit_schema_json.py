import json

from hs_cloudnative_schemas.schema.scripts.generate_resource_edit_schema_json import (
    OUTPUT_FILE,
    build_resource_edit_schema,
    write_resource_edit_schema,
)


def test_build_resource_edit_schema_uses_definitions_not_defs():
    schema = build_resource_edit_schema()
    schema_json = json.dumps(schema)

    assert "definitions" in schema
    assert "$defs" not in schema_json
    assert schema["properties"]["name"].get("readOnly") is not True
    assert schema["properties"]["@context"]["readOnly"] is True


def test_write_resource_edit_schema_writes_json_file(tmp_path):
    output_path = tmp_path / OUTPUT_FILE.name

    written_path = write_resource_edit_schema(output_path)

    assert written_path == output_path
    assert written_path.exists()

    schema = json.loads(written_path.read_text(encoding="utf-8"))
    assert "definitions" in schema
    assert "$defs" not in schema
    assert schema["title"] == "CoreMetadataEdit"