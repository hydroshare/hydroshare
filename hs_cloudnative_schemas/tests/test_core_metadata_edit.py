from hs_cloudnative_schemas.schema.core import CoreMetadataEdit


def _get_property(properties: dict, field_name: str) -> dict:
    if field_name in properties:
        return properties[field_name]

    alias_name = {
        "context": "@context",
        "type": "@type",
    }.get(field_name)
    if alias_name and alias_name in properties:
        return properties[alias_name]

    raise AssertionError(f"Property {field_name} not found in schema")


def test_core_metadata_edit_marks_only_non_editable_fields_as_read_only():
    schema = CoreMetadataEdit.model_json_schema()
    properties = schema["properties"]

    editable_fields = {
        "name",
        "description",
        "creator",
        "contributor",
        "keywords",
        "license",
        "subjectOf",
        "funding",
        "spatialCoverage",
        "temporalCoverage",
        "relation",
        "additionalProperty",
    }
    read_only_fields = {
        "context",
        "type",
        "additionalType",
        "url",
        "identifier",
        "dateCreated",
        "provider",
        "publisher",
        "datePublished",
        "version",
        "inLanguage",
        "creativeWorkStatus",
        "dateModified",
        "hasPart",
        "isPartOf",
        "associatedMedia",
        "citation",
    }

    expected_property_names = {
        "@context",
        "@type",
        "additionalType",
        "name",
        "description",
        "url",
        "identifier",
        "creator",
        "dateCreated",
        "keywords",
        "license",
        "provider",
        "contributor",
        "publisher",
        "datePublished",
        "subjectOf",
        "version",
        "inLanguage",
        "creativeWorkStatus",
        "dateModified",
        "funding",
        "temporalCoverage",
        "spatialCoverage",
        "hasPart",
        "isPartOf",
        "relation",
        "additionalProperty",
        "associatedMedia",
        "citation",
    }

    assert editable_fields.isdisjoint(read_only_fields)
    assert set(properties) == expected_property_names

    accounted_for_fields = editable_fields | read_only_fields
    assert accounted_for_fields == {
        "context",
        "type",
        "additionalType",
        "name",
        "description",
        "url",
        "identifier",
        "creator",
        "dateCreated",
        "keywords",
        "license",
        "provider",
        "contributor",
        "publisher",
        "datePublished",
        "subjectOf",
        "version",
        "inLanguage",
        "creativeWorkStatus",
        "dateModified",
        "funding",
        "temporalCoverage",
        "spatialCoverage",
        "hasPart",
        "isPartOf",
        "relation",
        "additionalProperty",
        "associatedMedia",
        "citation",
    }

    for field_name in editable_fields:
        assert _get_property(properties, field_name).get("readOnly") is not True

    for field_name in read_only_fields:
        assert _get_property(properties, field_name).get("readOnly") is True