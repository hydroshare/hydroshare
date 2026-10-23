from hs_cloudnative_schemas.schema.base import AdditionalPropertyValue
from hs_cloudnative_schemas.schema.core import CoreMetadataEdit


def test_additional_property_value_accepts_name_and_value():
    prop = AdditionalPropertyValue(name="Sensor", value="Temperature probe")
    assert prop.name == "Sensor"
    assert prop.value == "Temperature probe"
    assert prop.type == "PropertyValue"


def test_additional_property_value_accepts_optional_description():
    prop = AdditionalPropertyValue(name="Sensor", value="Temperature probe", description="A sensor")
    assert prop.description == "A sensor"


def test_additional_property_value_schema_has_only_expected_properties():
    schema = AdditionalPropertyValue.model_json_schema()
    assert set(schema["properties"]) == {"@type", "name", "value", "description"}
    assert schema["properties"]["value"]["type"] == "string"
    assert set(schema["required"]) == {"name", "value"}


def test_core_metadata_edit_additional_property_uses_trimmed_definition():
    schema = CoreMetadataEdit.model_json_schema()
    additional_property = schema["properties"]["additionalProperty"]
    array_schema = next(branch for branch in additional_property["anyOf"] if branch.get("type") == "array")
    assert array_schema["items"]["$ref"] == "#/$defs/AdditionalPropertyValue"
    assert set(schema["$defs"]["AdditionalPropertyValue"]["properties"]) == {
        "@type",
        "name",
        "value",
        "description",
    }
