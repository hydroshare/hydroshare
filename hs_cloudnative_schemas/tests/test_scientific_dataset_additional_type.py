import pytest
from pydantic import TypeAdapter, ValidationError

from hs_cloudnative_schemas.schema.dataset import AdditionalType, ScientificDataset

_adapter = TypeAdapter(ScientificDataset.model_fields["additionalType"].annotation)


def test_accepts_legacy_enum_value():
    assert _adapter.validate_python("GeographicRaster") == AdditionalType.GEOGRAPHIC_RASTER


def test_accepts_list_of_urls():
    urls = ["https://www.hydroshare.org/terms/CompositeResource",
            "https://www.hydroshare.org/terms/GeographicRasterAggregation"]
    assert [str(u) for u in _adapter.validate_python(urls)] == urls


def test_rejects_unknown_plain_string():
    with pytest.raises(ValidationError):
        _adapter.validate_python("NotAType")
