import pytest
from pydantic import ValidationError

from hs_cloudnative_schemas.schema.base import License, LicenseEnum
from hs_cloudnative_schemas.schema.core import CoreMetadataEdit


def _minimal_core_metadata_kwargs(license_value):
    return dict(
        name="Test resource",
        description="Test description",
        url="https://www.hydroshare.org/resource/abc123",
        identifier=["https://www.hydroshare.org/resource/abc123"],
        creator=[],
        dateCreated="2024-01-01T00:00:00Z",
        dateModified="2024-01-02T00:00:00Z",
        keywords=["water"],
        license=license_value,
        provider={"name": "HydroShare"},
    )


def test_license_accepts_known_enum_name():
    license_obj = License(name=LicenseEnum.CC_BY)
    assert license_obj.name == "Creative Commons Attribution CC BY"


def test_license_rejects_custom_name():
    with pytest.raises(ValidationError):
        License(name="My Custom License")


def test_core_metadata_edit_license_accepts_known_license():
    metadata = CoreMetadataEdit.model_validate(
        _minimal_core_metadata_kwargs({"name": "Creative Commons Attribution CC BY"})
    )
    assert metadata.license.name == LicenseEnum.CC_BY


def test_core_metadata_edit_license_accepts_custom_url():
    metadata = CoreMetadataEdit.model_validate(
        _minimal_core_metadata_kwargs("https://example.com/my-license")
    )
    assert str(metadata.license) == "https://example.com/my-license"


def test_core_metadata_edit_license_rejects_custom_name():
    with pytest.raises(ValidationError):
        CoreMetadataEdit.model_validate(
            _minimal_core_metadata_kwargs({"name": "My Custom License"})
        )


def test_generated_schema_exposes_license_enum():
    schema = CoreMetadataEdit.model_json_schema()
    license_enum = schema["$defs"]["LicenseEnum"]["enum"]
    assert license_enum == [
        "Creative Commons Attribution CC BY",
        "Creative Commons Attribution-ShareAlike CC BY-SA",
        "Creative Commons Attribution-NoDerivs CC BY-ND",
        "Creative Commons Attribution-NoCommercial-ShareAlike CC BY-NC-SA",
        "Creative Commons Attribution-NoCommercial CC BY-NC",
        "Creative Commons Attribution-NoCommercial-NoDerivs CC BY-NC-ND",
    ]
