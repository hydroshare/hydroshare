import pytest

from hs_cloudnative_schemas.schema.base import (
    CCBYLicense,
    CCBYSALicense,
    CCBYNDLicense,
    CCBYNCSALicense,
    CCBYNCLicense,
    CCBYNCNDLicense,
    OtherLicense,
    LicenseEnum,
)
from hs_cloudnative_schemas.schema.core import CoreMetadataEdit

STANDARD_LICENSE_CLASSES = [
    (LicenseEnum.CC_BY, CCBYLicense, "https://creativecommons.org/licenses/by/4.0/"),
    (LicenseEnum.CC_BY_SA, CCBYSALicense, "https://creativecommons.org/licenses/by-sa/4.0/"),
    (LicenseEnum.CC_BY_ND, CCBYNDLicense, "https://creativecommons.org/licenses/by-nd/4.0/"),
    (LicenseEnum.CC_BY_NC_SA, CCBYNCSALicense, "https://creativecommons.org/licenses/by-nc-sa/4.0/"),
    (LicenseEnum.CC_BY_NC, CCBYNCLicense, "https://creativecommons.org/licenses/by-nc/4.0/"),
    (LicenseEnum.CC_BY_NC_ND, CCBYNCNDLicense, "https://creativecommons.org/licenses/by-nc-nd/4.0/"),
]


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


@pytest.mark.parametrize("license_enum,license_cls,expected_url", STANDARD_LICENSE_CLASSES)
def test_standard_license_class_defaults(license_enum, license_cls, expected_url):
    license_obj = license_cls()
    assert license_obj.description == license_enum.value
    assert license_obj.name == f"This resource is shared under the {license_enum.value}."
    assert str(license_obj.url) == expected_url


@pytest.mark.parametrize("license_enum,license_cls,expected_url", STANDARD_LICENSE_CLASSES)
def test_standard_license_name_and_url_are_marked_read_only_in_schema(license_enum, license_cls, expected_url):
    # name/url are UI-read-only (pre-filled, not hand-edited) for standard licenses, so legacy/adapter-produced
    # values that don't exactly match the canonical text can still load and validate.
    schema = license_cls.model_json_schema()
    assert schema["properties"]["name"].get("readOnly") is True
    assert "const" not in schema["properties"]["name"]
    assert schema["properties"]["url"].get("readOnly") is True
    assert "const" not in schema["properties"]["url"]


def test_other_license_requires_name_but_url_is_optional():
    with pytest.raises(Exception):
        OtherLicense()
    license_obj = OtherLicense(name="My Custom License")
    assert license_obj.description == "Other"
    assert license_obj.name == "My Custom License"
    assert license_obj.url is None

    license_obj_with_url = OtherLicense(name="My Custom License", url="https://example.com/my-license")
    assert str(license_obj_with_url.url) == "https://example.com/my-license"


def test_core_metadata_edit_license_accepts_known_license():
    metadata = CoreMetadataEdit.model_validate(
        _minimal_core_metadata_kwargs({"description": "Creative Commons Attribution CC BY"})
    )
    assert isinstance(metadata.license, CCBYLicense)
    assert metadata.license.description == LicenseEnum.CC_BY.value


def test_core_metadata_edit_license_accepts_other_license():
    metadata = CoreMetadataEdit.model_validate(
        _minimal_core_metadata_kwargs(
            {"description": "Other", "name": "All rights reserved.", "url": "https://example.com/my-license"}
        )
    )
    assert isinstance(metadata.license, OtherLicense)
    assert metadata.license.name == "All rights reserved."
    assert str(metadata.license.url) == "https://example.com/my-license"


def test_generated_schema_exposes_license_union():
    schema = CoreMetadataEdit.model_json_schema()
    license_refs = {ref["$ref"].rsplit("/", 1)[-1] for ref in schema["properties"]["license"]["anyOf"]}
    assert license_refs == {
        "CCBYLicense",
        "CCBYSALicense",
        "CCBYNDLicense",
        "CCBYNCSALicense",
        "CCBYNCLicense",
        "CCBYNCNDLicense",
        "OtherLicense",
    }
    descriptions = {
        schema["$defs"][ref]["properties"]["description"]["default"] for ref in license_refs
    }
    assert descriptions == {
        "Creative Commons Attribution CC BY",
        "Creative Commons Attribution-ShareAlike CC BY-SA",
        "Creative Commons Attribution-NoDerivs CC BY-ND",
        "Creative Commons Attribution-NoCommercial-ShareAlike CC BY-NC-SA",
        "Creative Commons Attribution-NoCommercial CC BY-NC",
        "Creative Commons Attribution-NoCommercial-NoDerivs CC BY-NC-ND",
        "Other",
    }


@pytest.mark.parametrize("license_enum", list(LicenseEnum))
def test_from_statement_accepts_known_license_statements(license_enum):
    statement = f"This resource is shared under the {license_enum.value}."
    assert LicenseEnum.from_statement(statement) == license_enum


def test_from_statement_strips_surrounding_whitespace():
    statement = "  This resource is shared under the Creative Commons Attribution CC BY.  "
    assert LicenseEnum.from_statement(statement) == LicenseEnum.CC_BY


def test_from_statement_returns_none_for_unknown_license_name():
    statement = "This resource is shared under the Made Up License."
    assert LicenseEnum.from_statement(statement) is None


def test_from_statement_returns_none_for_statement_without_known_prefix():
    assert LicenseEnum.from_statement("All rights reserved.") is None
