import uuid

from hsextract.content_types.models import BaseMetadataObject
from hsextract.main import write_resource_jsonld_metadata
from tests import read_s3_json, write_s3_json


def _make_resource_metadata_object(resource_id: str) -> BaseMetadataObject:
    return BaseMetadataObject(
        f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json", True
    )


def _system_metadata_json(resource_id: str) -> dict:
    # Mirrors the fields/keys used in system_metadata.json
    return {
        "resource_id": resource_id,
        "doi": "10.4211/hs.system-doi",
        "created": "2024-01-01T00:00:00",
        "modified": "2024-06-01T00:00:00",
        "status": {
            "public": True,
            "discoverable": True,
            "published": False,
            "shareable": True,
        },
    }


def test_system_metadata_wins_on_key_conflict():
    resource_id = str(uuid.uuid4())
    md = _make_resource_metadata_object(resource_id)

    system_json = _system_metadata_json(resource_id)
    write_s3_json(md.system_metadata_path, system_json)
    write_s3_json(
        md.user_metadata_path,
        {
            "doi": "10.4211/hs.user-supplied-doi",
            "modified": "2099-12-31T00:00:00",
            "abstract": "user abstract",
        },
    )

    write_resource_jsonld_metadata(md)

    result = read_s3_json(md.resource_metadata_jsonld_path)

    # system metadata value must win over the conflicting user metadata value
    assert result["doi"] == system_json["doi"]
    assert result["modified"] == system_json["modified"]
    # non-conflicting key from user metadata is preserved
    assert result["abstract"] == "user abstract"


def test_combined_metadata_preserves_all_system_metadata_unchanged():
    resource_id = str(uuid.uuid4())
    md = _make_resource_metadata_object(resource_id)

    system_json = _system_metadata_json(resource_id)
    write_s3_json(md.system_metadata_path, system_json)
    write_s3_json(
        md.user_metadata_path,
        {
            "resource_id": "not-the-real-id",
            "doi": "10.4211/hs.user-supplied-doi",
            "created": "2099-01-01T00:00:00",
            "modified": "2099-12-31T00:00:00",
            "status": {
                "public": False,
                "discoverable": False,
                "published": True,
                "shareable": False,
            },
        },
    )

    write_resource_jsonld_metadata(md)

    result = read_s3_json(md.resource_metadata_jsonld_path)

    # every key/value pair from system metadata (including the nested "status" dict)
    # must be present in the result, untouched, regardless of what user metadata
    # contains for those same keys
    for key, value in system_json.items():
        assert result[key] == value
