import datetime

import pytest

from pydantic import HttpUrl

from . import utils


@pytest.mark.asyncio
async def test_core_schema(core_data, core_model):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model. Note: This test does nat
    add a record to the database.
    """
    core_data = core_data
    core_model = core_model

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)

    assert core_model_instance.name == "Test Dataset"


@pytest.mark.parametrize("multiple_creators", [True, False])
@pytest.mark.parametrize("creator_type", ["person", "organization"])
@pytest.mark.asyncio
async def test_core_schema_creator_cardinality(
    core_data, core_model, multiple_creators, creator_type
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we can have one or
    more creators. Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    core_data.pop("creator")
    if multiple_creators:
        if creator_type == "person":
            core_data["creator"] = [
                {"@type": "Person", "name": "John Doe",
                    "email": "john.doe@gmail.com"},
                {
                    "@type": "Person",
                    "name": "Jane Doe",
                    "email": "jan.doe@gmail.com",
                    "affiliation": {
                        "@type": "Organization",
                        "name": "Utah State University",
                        "url": "https://www.usu.edu/",
                        "address": "Logan, UT 84322",
                    },
                },
            ]
        else:
            core_data["creator"] = [
                {
                    "@type": "Organization",
                    "name": "National Centers for Environmental Information",
                    "url": "https://www.ncei.noaa.gov/",
                },
                {
                    "@type": "Organization",
                    "name": "National Oceanic and Atmospheric Administration",
                    "url": "https://www.noaa.gov/",
                    "address": "1315 East-West Highway, Silver Spring, MD 20910",
                },
            ]
    else:
        if creator_type == "person":
            core_data["creator"] = [
                {
                    "@type": "Person",
                    "name": "John Doe",
                    "email": "john.doe@gmail.com",
                }
            ]
        else:
            core_data["creator"] = [
                {
                    "@type": "Organization",
                    "name": "National Centers for Environmental Information",
                    "url": "https://www.ncei.noaa.gov/",
                }
            ]

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)

    if multiple_creators:
        if creator_type == "person":
            assert len(core_model_instance.creator) == 2
            assert core_model_instance.creator[0].type == "Person"
            assert core_model_instance.creator[1].type == "Person"
            assert core_model_instance.creator[0].name == "John Doe"
            assert core_model_instance.creator[1].name == "Jane Doe"
            assert core_model_instance.creator[0].email == "john.doe@gmail.com"
            assert core_model_instance.creator[1].email == "jan.doe@gmail.com"
            assert core_model_instance.creator[
                1].affiliation.type == "Organization"
            assert (
                core_model_instance.creator[1].affiliation.name
                == "Utah State University"
            )
            assert core_model_instance.creator[1].affiliation.url == HttpUrl(
                "https://www.usu.edu/"
            )
            assert (
                core_model_instance.creator[
                    1].affiliation.address == "Logan, UT 84322"
            )
        else:
            assert len(core_model_instance.creator) == 2
            assert core_model_instance.creator[0].type == "Organization"
            assert core_model_instance.creator[1].type == "Organization"
            assert (
                core_model_instance.creator[0].name
                == "National Centers for Environmental Information"
            )
            assert (
                core_model_instance.creator[1].name
                == "National Oceanic and Atmospheric Administration"
            )
            assert core_model_instance.creator[0].url == HttpUrl(
                "https://www.ncei.noaa.gov/"
            )
            assert core_model_instance.creator[1].url == HttpUrl(
                "https://www.noaa.gov/"
            )
            assert (
                core_model_instance.creator[1].address
                == "1315 East-West Highway, Silver Spring, MD 20910"
            )
    else:
        if creator_type == "person":
            assert core_model_instance.creator[0].type == "Person"
            assert core_model_instance.creator[0].name == "John Doe"
            assert core_model_instance.creator[0].email == "john.doe@gmail.com"
        else:
            assert core_model_instance.creator[0].type == "Organization"
            assert (
                core_model_instance.creator[0].name
                == "National Centers for Environmental Information"
            )
            assert core_model_instance.creator[0].url == HttpUrl(
                "https://www.ncei.noaa.gov/"
            )


@pytest.mark.parametrize(
    "data_format",
    [
        {"@type": "Person", "name": "John Doe"},
        {"@type": "Person", "name": "John Doe", "email": "john.doe@gmail.com"},
        {
            "@type": "Person",
            "name": "John Doe",
            "email": "john.doe@gmail.com",
            "affiliation": {
                "@type": "Organization",
                "name": "NC State University",
                "url": "https://www.ncsu.edu/",
                "address": "Raleigh, NC 27695",
            },
        },
        {
            "@type": "Person",
            "name": "John Doe",
            "identifier": "https://orcid.org/0000-0002-1825-0097",
        },
    ],
)
@pytest.mark.asyncio
async def test_core_schema_creator_person_optional_attributes(
    core_data, core_model, data_format
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    email and identifier attributes are optional. Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    core_data.pop("creator")
    core_data["creator"] = [data_format]

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)

    assert core_model_instance.creator[0].type == "Person"
    assert core_model_instance.creator[0].name == "John Doe"
    if "email" in data_format:
        assert core_model_instance.creator[0].email == "john.doe@gmail.com"
    if "identifier" in data_format:
        assert (
            core_model_instance.creator[0].identifier
            == "https://orcid.org/0000-0002-1825-0097"
        )
    if "affiliation" in data_format:
        assert core_model_instance.creator[
            0].affiliation.type == "Organization"
        assert core_model_instance.creator[
            0].affiliation.name == "NC State University"
        assert core_model_instance.creator[0].affiliation.url == HttpUrl(
            "https://www.ncsu.edu/"
        )
        assert core_model_instance.creator[
            0].affiliation.address == "Raleigh, NC 27695"


@pytest.mark.parametrize(
    "data_format",
    [
        {
            "@type": "Person",
            "name": "John Doe",
            "email": "john.doe@gmail.com",
            "affiliation": {
                "@type": "Organization",
                "name": "NC State University",
                "url": "https://www.ncsu.edu/",
                "address": "Raleigh, NC 27695",
            },
        },
        {
            "@type": "Person",
            "name": "John Doe",
            "email": "john.doe@gmail.com",
            "affiliation": {
                "@type": "Organization",
                "name": "NC State University",
                "url": "https://www.ncsu.edu/",
            },
        },
        {
            "@type": "Person",
            "name": "John Doe",
            "email": "john.doe@gmail.com",
            "affiliation": {
                "@type": "Organization",
                "name": "NC State University",
                "address": "Raleigh, NC 27695",
            },
        },
    ],
)
@pytest.mark.asyncio
async def test_core_schema_creator_affiliation_optional_attributes(
    core_data, core_model, data_format
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    creator affiliation optional attributes. Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    core_data.pop("creator")
    core_data["creator"] = [data_format]

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)

    assert core_model_instance.creator[0].type == "Person"
    assert core_model_instance.creator[0].name == "John Doe"
    assert core_model_instance.creator[0].email == "john.doe@gmail.com"
    assert core_model_instance.creator[0].affiliation.type == "Organization"
    assert core_model_instance.creator[
        0].affiliation.name == "NC State University"
    if "url" in data_format:
        assert core_model_instance.creator[0].affiliation.url == HttpUrl(
            "https://www.ncsu.edu/"
        )
    if "address" in data_format:
        assert core_model_instance.creator[
            0].affiliation.address == "Raleigh, NC 27695"


@pytest.mark.parametrize(
    "data_format",
    [
        {
            "@type": "Organization",
            "name": "National Centers for Environmental Information",
        },
        {
            "@type": "Organization",
            "name": "National Centers for Environmental Information",
            "address": "1167 Massachusetts Ave Suites 418 & 419, Arlington, MA 02476",
        },
        {
            "@type": "Organization",
            "name": "National Centers for Environmental Information",
            "url": "https://www.ncei.noaa.gov/",
        },
        {
            "@type": "Organization",
            "name": "National Centers for Environmental Information",
            "url": "https://www.ncei.noaa.gov/",
            "address": "1167 Massachusetts Ave Suites 418 & 419, Arlington, MA 02476",
        },
    ],
)
@pytest.mark.asyncio
async def test_core_schema_creator_organization_optional_attributes(
    core_data, core_model, data_format
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    optional attributes of the organization object. Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    core_data.pop("creator")
    core_data["creator"] = [data_format]

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    assert core_model_instance.creator[0].type == "Organization"
    assert (
        core_model_instance.creator[0].name
        == "National Centers for Environmental Information"
    )
    if "url" in data_format:
        assert core_model_instance.creator[0].url == HttpUrl(
            "https://www.ncei.noaa.gov/"
        )
    if "address" in data_format:
        assert (
            core_model_instance.creator[0].address
            == "1167 Massachusetts Ave Suites 418 & 419, Arlington, MA 02476"
        )


@pytest.mark.parametrize("multiple_media", [True, False, None])
@pytest.mark.asyncio
async def test_core_schema_associated_media_cardinality(
    core_data, core_model, multiple_media
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    one or more associated media objects can be created. Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    if multiple_media is None:
        core_data.pop("associatedMedia", None)
    if multiple_media and multiple_media is not None:
        associated_media = [
            {
                "@type": "DataDownload",
                "contentUrl": "https://www.hydroshare.org/resource/51d1539bf6e94b15ac33f7631228118c/data/contents/USGS_Harvey_gages_TxLaMsAr.csv",
                "encodingFormat": "text/csv",
                "contentSize": "0.17 GB",
                "sha256": "2fba6f2ebac562dac6a57acf0fdc5fdfabc9654b3c910aa6ef69cf4385997e19",
                "name": "USGS gage locations within the Harvey-affected areas in Texas",
            },
            {
                "@type": "VideoObject",
                "contentUrl": "https://www.hydroshare.org/resource/81cb3f6c0dde4433ae4f43a26a889864/data/contents/HydroClientMovie.mp4",
                "encodingFormat": "video/mp4",
                "contentSize": "79.2 MB",
                "sha256": "2fba6f2ebac562dac6a57acf0fdc5fdfabc9654b3c910aa6ef69cf4385997e20",
                "name": "HydroClient Video",
            },
        ]

        core_data["associatedMedia"] = associated_media

    elif multiple_media is not None:
        associated_media = [
            {
                "@type": "MediaObject",
                "contentUrl": "https://www.hydroshare.org/resource/51d1539bf6e94b15ac33f7631228118c/data/contents/USGS_Harvey_gages_TxLaMsAr.csv",
                "encodingFormat": "text/csv",
                "contentSize": "0.17 MB",
                "sha256": "2fba6f2ebac562dac6a57acf0fdc5fdfabc9654b3c910aa6ef69cf4385997e19",
                "name": "USGS gage locations within the Harvey-affected areas in Texas",
            }
        ]
        core_data["associatedMedia"] = associated_media

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)

    if multiple_media is None:
        assert core_model_instance.associatedMedia is None
    if multiple_media and multiple_media is not None:
        assert len(core_model_instance.associatedMedia) == 2
        assert (
            core_model_instance.associatedMedia[
                0].type == associated_media[0]["@type"]
        )
        assert (
            core_model_instance.associatedMedia[
                1].type == associated_media[1]["@type"]
        )
        assert (
            core_model_instance.associatedMedia[
                0].name == associated_media[0]["name"]
        )
        assert (
            core_model_instance.associatedMedia[
                1].name == associated_media[1]["name"]
        )
        assert (
            core_model_instance.associatedMedia[0].contentSize
            == associated_media[0]["contentSize"]
        )
        assert (
            core_model_instance.associatedMedia[1].contentSize
            == associated_media[1]["contentSize"]
        )
        assert (
            core_model_instance.associatedMedia[0].encodingFormat
            == associated_media[0]["encodingFormat"]
        )
        assert (
            core_model_instance.associatedMedia[1].encodingFormat
            == associated_media[1]["encodingFormat"]
        )
        assert core_model_instance.associatedMedia[0].contentUrl == HttpUrl(
            associated_media[0]["contentUrl"]
        )
        assert core_model_instance.associatedMedia[1].contentUrl == HttpUrl(
            associated_media[1]["contentUrl"]
        )
        assert (
            core_model_instance.associatedMedia[0].sha256
            == associated_media[0]["sha256"]
        )
        assert (
            core_model_instance.associatedMedia[1].sha256
            == associated_media[1]["sha256"]
        )
    elif multiple_media is not None:
        assert (
            core_model_instance.associatedMedia[
                0].type == associated_media[0]["@type"]
        )
        assert (
            core_model_instance.associatedMedia[
                0].name == associated_media[0]["name"]
        )
        assert (
            core_model_instance.associatedMedia[0].contentSize
            == associated_media[0]["contentSize"]
        )
        assert (
            core_model_instance.associatedMedia[0].encodingFormat
            == associated_media[0]["encodingFormat"]
        )
        assert core_model_instance.associatedMedia[0].contentUrl == HttpUrl(
            associated_media[0]["contentUrl"]
        )
        assert (
            core_model_instance.associatedMedia[0].sha256
            == associated_media[0]["sha256"]
        )


@pytest.mark.parametrize(
    "content_size_format",
    [
        "100.17 KB",
        "100.17kilobytes",
        ".89 KB",
        "0.89 KB",
        "100.17 MB",
        "100.17 megabytes",
        "100.17 GB",
        "100.17 gigabytes",
        "100.17 TB",
        "100.17 terabytes",
        "100.17 PB",
        "10.170 petabytes",
    ],
)
@pytest.mark.asyncio
async def test_core_schema_associated_media_content_size(
    core_data, core_model, content_size_format
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    valid values for the contentSize attribute of the associatedMedia property.
    Note: This test does nat add a record to the database.
    """

    core_data = core_data
    core_model = core_model

    core_data["associatedMedia"] = [
        {
            "@type": "MediaObject",
            "contentUrl": "https://www.hydroshare.org/resource/51d1539bf6e94b15ac33f7631228118c/data/contents/USGS_Harvey_gages_TxLaMsAr.csv",
            "encodingFormat": "text/csv",
            "contentSize": content_size_format,
            "sha256": "2fba6f2ebac562dac6a57acf0fdc5fdfabc9654b3c910aa6ef69cf4385997e19",
            "name": "USGS gage locations within the Harvey-affected areas in Texas",
        }
    ]

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    assert core_model_instance.associatedMedia[
        0].contentSize == content_size_format


@pytest.mark.parametrize("include_coverage", [True, False])
@pytest.mark.asyncio
async def test_core_schema_temporal_coverage_optional(
    core_data, core_model, include_coverage
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    temporal coverage can be optional.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    coverage_value = {
        "startDate": "2007-03-01T13:00:00",
        "endDate": "2008-05-11T15:30:00",
    }
    core_data.pop("temporalCoverage", None)
    if not include_coverage:
        core_data.pop("temporalCoverage", None)
    else:
        core_data["temporalCoverage"] = coverage_value

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    if not include_coverage:
        assert core_model_instance.temporalCoverage is None
    else:
        assert core_model_instance.temporalCoverage.startDate == datetime.datetime(
            2007, 3, 1, 13, 0, 0
        )
        assert core_model_instance.temporalCoverage.endDate == datetime.datetime(
            2008, 5, 11, 15, 30, 0
        )


@pytest.mark.parametrize(
    "data_format",
    [
        {"startDate": "2007-03-01T13:00:00", "endDate": "2008-05-11T15:30:00"},
        {"startDate": "2007-03-01T13:00:00"},
    ],
)
@pytest.mark.asyncio
async def test_core_schema_temporal_coverage_format(core_data, core_model, data_format):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    that endDate is optional for temporal coverage.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    core_data["temporalCoverage"] = data_format

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    assert core_model_instance.temporalCoverage.startDate == datetime.datetime(
        2007, 3, 1, 13, 0, 0
    )
    if "endDate" in data_format:
        assert core_model_instance.temporalCoverage.endDate == datetime.datetime(
            2008, 5, 11, 15, 30, 0
        )
    else:
        assert core_model_instance.temporalCoverage.endDate is None


@pytest.mark.parametrize("include_coverage", [True, False])
@pytest.mark.asyncio
async def test_core_schema_spatial_coverage_optional(
    core_data, core_model, include_coverage
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    spatial coverage can be optional.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    coverage_value = {
        "@type": "Place",
        "name": "CUAHSI Office",
        "geo": {"@type": "GeoCoordinates", "latitude": 42.4127, "longitude": -71.1197},
    }

    if not include_coverage:
        core_data.pop("spatialCoverage", None)
    else:
        core_data["spatialCoverage"] = coverage_value

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    if not include_coverage:
        assert core_model_instance.spatialCoverage is None
    else:
        assert core_model_instance.spatialCoverage.type == coverage_value[
            "@type"]
        assert core_model_instance.spatialCoverage.name == coverage_value[
            "name"]
        geo = core_model_instance.spatialCoverage.geo
        assert geo.type == coverage_value["geo"]["@type"]
        assert geo.latitude == coverage_value["geo"]["latitude"]
        assert geo.longitude == coverage_value["geo"]["longitude"]


@pytest.mark.parametrize(
    "data_format",
    [
        {"@type": "Place", "name": "CUAHSI Office"},
        {
            "@type": "Place",
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": 39.3280,
                "longitude": 120.1633,
            },
        },
        {
            "@type": "Place",
            "geo": {"@type": "GeoShape", "box": "39.3280 120.1633 40.445 123.7878"},
        },
        {
            "@type": "Place",
            "name": "Logan Watershed",
            "geo": {
                "@type": "GeoShape",
                "box": "41.70049003694901 -111.78438452093438 42.102360645589236 -111.51208495002092",
            },
            "additionalProperty": [
                {
                    "@type": "PropertyValue",
                    "name": "Geographic Coordinate System",
                    "value": "WGS 84 EPSG:4326",
                },
            ],
        },
        {
            "@type": "Place",
            "name": "Logan Watershed",
            "geo": {
                "@type": "GeoShape",
                "box": "41.70049003694901 -111.78438452093438 42.102360645589236 -111.51208495002092",
            },
            "additionalProperty": [
                {
                    "@type": "PropertyValue",
                    "name": "Projected Coordinate System",
                    "value": "WGS_1984_UTM_Zone_12N",
                },
                {
                    "@type": "PropertyValue",
                    "name": "Datum",
                    "value": "WGS_1984",
                },
            ],
        },
    ],
)
@pytest.mark.asyncio
async def test_core_schema_spatial_coverage_value_type(
    core_data, core_model, data_format
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    valid values for spatial coverage with optional additionalProperty attribute.
    Note: This test does not add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    core_data["spatialCoverage"] = data_format
    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)

    assert core_model_instance.spatialCoverage.type == "Place"
    if "name" in data_format:
        assert core_model_instance.spatialCoverage.name == data_format["name"]
    if "geo" in data_format:
        if data_format["geo"]["@type"] == "GeoCoordinates":
            assert (
                core_model_instance.spatialCoverage.geo.latitude
                == data_format["geo"]["latitude"]
            )
            assert (
                core_model_instance.spatialCoverage.geo.longitude
                == data_format["geo"]["longitude"]
            )
        elif data_format["geo"]["@type"] == "GeoShape":
            assert (
                core_model_instance.spatialCoverage.geo.box == data_format[
                    "geo"]["box"]
            )
    if "additionalProperty" in data_format:
        if len(core_model_instance.spatialCoverage.additionalProperty) == 1:
            assert (
                core_model_instance.spatialCoverage.additionalProperty[0].name
                == "Geographic Coordinate System"
            )
            assert (
                core_model_instance.spatialCoverage.additionalProperty[0].type
                == "PropertyValue"
            )
            assert (
                core_model_instance.spatialCoverage.additionalProperty[0].value
                == "WGS 84 EPSG:4326"
            )
        else:
            assert len(
                core_model_instance.spatialCoverage.additionalProperty) == 2
            assert (
                core_model_instance.spatialCoverage.additionalProperty[0].type
                == "PropertyValue"
            )
            assert (
                core_model_instance.spatialCoverage.additionalProperty[0].name
                == "Projected Coordinate System"
            )
            assert (
                core_model_instance.spatialCoverage.additionalProperty[0].value
                == "WGS_1984_UTM_Zone_12N"
            )
            assert (
                core_model_instance.spatialCoverage.additionalProperty[1].type
                == "PropertyValue"
            )
            assert (
                core_model_instance.spatialCoverage.additionalProperty[1].name
                == "Datum"
            )
            assert (
                core_model_instance.spatialCoverage.additionalProperty[1].value
                == "WGS_1984"
            )
    else:
        assert core_model_instance.spatialCoverage.additionalProperty == []


@pytest.mark.parametrize("include_creative_works", [True, False])
@pytest.mark.asyncio
async def test_create_dataset_creative_works_status_optional(
    core_data, core_model, include_creative_works
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    creativeWorkStatus can be optional.
    Note: This test does nat add a record to the database.
    """

    core_data = core_data
    core_model = core_model
    if not include_creative_works:
        core_data.pop("creativeWorkStatus", None)
    else:
        core_data["creativeWorkStatus"] = {
            "@type": "DefinedTerm",
            "name": "Draft",
            "description": "This is a draft dataset",
        }

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    if not include_creative_works:
        assert core_model_instance.creativeWorkStatus is None
    else:
        assert core_model_instance.creativeWorkStatus.type == "DefinedTerm"
        assert core_model_instance.creativeWorkStatus.name == "Draft"
        assert (
            core_model_instance.creativeWorkStatus.description
            == "This is a draft dataset"
        )


@pytest.mark.parametrize("include_multiple", [True, False])
@pytest.mark.asyncio
async def test_core_schema_keywords_cardinality(
    core_data, core_model, include_multiple
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    that one or more keywords can be added.
    Note: This test does nat add a record to the database.
    """

    core_data = core_data
    core_model = core_model
    core_data.pop("keywords", None)
    if include_multiple:
        core_data["keywords"] = ["Leaf wetness", "Core"]
    else:
        core_data["keywords"] = ["Leaf wetness"]

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    if include_multiple:
        assert len(core_model_instance.keywords) == 2
        assert core_model_instance.keywords[0] == "Leaf wetness"
        assert core_model_instance.keywords[1] == "Core"
    else:
        assert len(core_model_instance.keywords) == 1
        assert core_model_instance.keywords[0] == "Leaf wetness"


@pytest.mark.skip(reason="Not sure if we need to support URL format for license.")
@pytest.mark.parametrize(
    "data_format",
    [
        "https://creativecommons.org/licenses/by/4.0/",
        {
            "@type": "CreativeWork",
            "name": "MIT License",
            "url": "https://spdx.org/licenses/MIT",
            "description": "A permissive license that is short and to the point. It lets people do anything with your code with proper attribution and without warranty.",
        },
    ],
)
@pytest.mark.asyncio
async def test_core_schema_license_value_type(core_data, core_model, data_format):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    valid value types for license property.
    Note: This test does nat add a record to the database.
    """

    core_data = core_data
    core_model = core_model
    core_data["license"] = data_format
    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    if isinstance(data_format, str):
        assert core_model_instance.license == data_format
    else:
        assert core_model_instance.license.type == data_format["@type"]
        assert core_model_instance.license.name == data_format["name"]
        assert core_model_instance.license.url == HttpUrl(data_format["url"])
        assert core_model_instance.license.description == data_format[
            "description"]


@pytest.mark.parametrize(
    "data_format",
    [
        {
            "@type": "CreativeWork",
            "name": "MIT License",
            "url": "https://spdx.org/licenses/MIT",
            "description": "A permissive license that is short and to the point. It lets people do anything with your code with proper attribution and without warranty.",
        },
        {
            "@type": "CreativeWork",
            "name": "MIT License",
            "url": "https://spdx.org/licenses/MIT",
        },
        {
            "@type": "CreativeWork",
            "name": "MIT License",
            "description": "A permissive license that is short and to the point. It lets people do anything with your code with proper attribution and without warranty.",
        },
        {"@type": "CreativeWork", "name": "MIT License"},
    ],
)
@pytest.mark.asyncio
async def test_core_schema_license_optional_attributes(
    core_data, core_model, data_format
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    license of type CreativeWork optional attributes.
    Note: This test does nat add a record to the database.
    """

    core_data = core_data
    core_model = core_model
    core_data["license"] = data_format
    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)

    assert core_model_instance.license.type == data_format["@type"]
    assert core_model_instance.license.name == data_format["name"]
    if "url" in data_format:
        assert core_model_instance.license.url == HttpUrl(data_format["url"])
    if "description" in data_format:
        assert core_model_instance.license.description == data_format[
            "description"]


@pytest.mark.parametrize("is_multiple", [True, False, None])
@pytest.mark.asyncio
async def test_core_schema_has_part_of_cardinality(core_data, core_model, is_multiple):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    that the hasPartOf property is optional and one or more values can be added for this property.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    core_data.pop("hasPart", None)

    has_parts = []
    if is_multiple and is_multiple is not None:
        has_parts = [
            {
                "@type": "CreativeWork",
                "name": "Great Salt Lake Bathymetry",
                "description": "Digital Elevation Model for the Great Salt Lake, lake bed bathymetry.",
                "url": "https://www.hydroshare.org/resource/582060f00f6b443bb26e896426d9f62a/",
            },
            {
                "@type": "CreativeWork",
                "name": "Great Salt Lake Level and Volume",
                "description": "Time series of level, area and volume in the Great Salt Lake.",
                "url": "https://www.hydroshare.org/resource/582060f00f6b443bb26e896426d9f62b/",
            },
        ]
        core_data["hasPart"] = has_parts
    elif is_multiple is not None:
        has_parts = [
            {
                "@type": "CreativeWork",
                "name": "Great Salt Lake Bathymetry",
                "description": "Digital Elevation Model for the Great Salt Lake, lake bed bathymetry.",
                "url": "https://www.hydroshare.org/resource/582060f00f6b443bb26e896426d9f62a/",
            }
        ]
        core_data["hasPart"] = has_parts

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    if is_multiple and is_multiple is not None:
        assert len(core_model_instance.hasPart) == 2
        assert core_model_instance.hasPart[0].type == has_parts[0]["@type"]
        assert core_model_instance.hasPart[1].type == has_parts[1]["@type"]
        assert core_model_instance.hasPart[0].name == has_parts[0]["name"]
        assert core_model_instance.hasPart[1].name == has_parts[1]["name"]
        assert core_model_instance.hasPart[
            0].description == has_parts[0]["description"]
        assert core_model_instance.hasPart[
            1].description == has_parts[1]["description"]
        assert core_model_instance.hasPart[
            0].url == HttpUrl(has_parts[0]["url"])
        assert core_model_instance.hasPart[
            1].url == HttpUrl(has_parts[1]["url"])
    elif is_multiple is not None:
        assert len(core_model_instance.hasPart) == 1
        assert core_model_instance.hasPart[0].type == has_parts[0]["@type"]
        assert core_model_instance.hasPart[0].name == has_parts[0]["name"]
        assert core_model_instance.hasPart[
            0].description == has_parts[0]["description"]
        assert core_model_instance.hasPart[
            0].url == HttpUrl(has_parts[0]["url"])
    else:
        assert core_model_instance.hasPart is None


@pytest.mark.parametrize(
    "data_format",
    [
        {
            "@type": "CreativeWork",
            "name": "Great Salt Lake Bathymetry",
            "description": "Digital Elevation Model for the Great Salt Lake, lake bed bathymetry.",
            "url": "https://www.hydroshare.org/resource/582060f00f6b443bb26e896426d9f62a/",
        },
        {
            "@type": "CreativeWork",
            "name": "Great Salt Lake Bathymetry",
            "description": "Digital Elevation Model for the Great Salt Lake, lake bed bathymetry.",
        },
        {
            "@type": "CreativeWork",
            "name": "Great Salt Lake Bathymetry",
            "url": "https://www.hydroshare.org/resource/582060f00f6b443bb26e896426d9f62a/",
        },
        {"@type": "CreativeWork", "name": "Great Salt Lake Bathymetry"},
    ],
)
@pytest.mark.asyncio
async def test_core_schema_has_part_optional_attributes(
    core_data, core_model, data_format
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    the optional attributes of hasPart property.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    core_data.pop("hasPart", None)
    core_data["hasPart"] = [data_format]

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    assert core_model_instance.hasPart[0].type == data_format["@type"]
    assert core_model_instance.hasPart[0].name == data_format["name"]
    if "description" in data_format:
        assert core_model_instance.hasPart[
            0].description == data_format["description"]
    if "url" in data_format:
        assert core_model_instance.hasPart[
            0].url == HttpUrl(data_format["url"])


@pytest.mark.parametrize("is_multiple", [True, False, None])
@pytest.mark.asyncio
async def test_core_schema_is_part_of_cardinality(core_data, core_model, is_multiple):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    that the isPartOf property is optional and one or more values can be added for this property.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    core_data.pop("isPartOf", None)
    is_part_of = []
    if is_multiple and is_multiple is not None:
        is_part_of = [
            {
                "@type": "CreativeWork",
                "name": "Great Salt Lake Bathymetry",
                "description": "Digital Elevation Model for the Great Salt Lake, lake bed bathymetry.",
                "url": "https://www.hydroshare.org/resource/582060f00f6b443bb26e896426d9f62a/",
            },
            {
                "@type": "CreativeWork",
                "name": "Great Salt Lake Level and Volume",
                "description": "Time series of level, area and volume in the Great Salt Lake.",
                "url": "https://www.hydroshare.org/resource/582060f00f6b443bb26e896426d9f62b/",
            },
        ]
        core_data["isPartOf"] = is_part_of
    elif is_multiple is not None:
        is_part_of = [
            {
                "@type": "CreativeWork",
                "name": "Great Salt Lake Bathymetry",
                "description": "Digital Elevation Model for the Great Salt Lake, lake bed bathymetry.",
                "url": "https://www.hydroshare.org/resource/582060f00f6b443bb26e896426d9f62a/",
            }
        ]
        core_data["isPartOf"] = is_part_of

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    if is_multiple and is_multiple is not None:
        assert len(core_model_instance.isPartOf) == 2
        assert core_model_instance.isPartOf[0].type == is_part_of[0]["@type"]
        assert core_model_instance.isPartOf[1].type == is_part_of[1]["@type"]
        assert core_model_instance.isPartOf[0].name == is_part_of[0]["name"]
        assert core_model_instance.isPartOf[1].name == is_part_of[1]["name"]
        assert (
            core_model_instance.isPartOf[
                0].description == is_part_of[0]["description"]
        )
        assert (
            core_model_instance.isPartOf[
                1].description == is_part_of[1]["description"]
        )
        assert core_model_instance.isPartOf[
            0].url == HttpUrl(is_part_of[0]["url"])
        assert core_model_instance.isPartOf[
            1].url == HttpUrl(is_part_of[1]["url"])
    elif is_multiple is not None:
        assert len(core_model_instance.isPartOf) == 1
        assert core_model_instance.isPartOf[0].type == is_part_of[0]["@type"]
        assert core_model_instance.isPartOf[0].name == is_part_of[0]["name"]
        assert (
            core_model_instance.isPartOf[
                0].description == is_part_of[0]["description"]
        )
        assert core_model_instance.isPartOf[
            0].url == HttpUrl(is_part_of[0]["url"])
    else:
        assert core_model_instance.isPartOf is None


@pytest.mark.parametrize(
    "data_format",
    [
        {
            "@type": "CreativeWork",
            "name": "Great Salt Lake Bathymetry",
            "description": "Digital Elevation Model for the Great Salt Lake, lake bed bathymetry.",
            "url": "https://www.hydroshare.org/resource/582060f00f6b443bb26e896426d9f62a/",
        },
        {
            "@type": "CreativeWork",
            "name": "Great Salt Lake Bathymetry",
            "description": "Digital Elevation Model for the Great Salt Lake, lake bed bathymetry.",
        },
        {
            "@type": "CreativeWork",
            "name": "Great Salt Lake Bathymetry",
            "url": "https://www.hydroshare.org/resource/582060f00f6b443bb26e896426d9f62a/",
        },
        {"@type": "CreativeWork", "name": "Great Salt Lake Bathymetry"},
    ],
)
@pytest.mark.asyncio
async def test_core_schema_is_part_of_optional_attributes(
    core_data, core_model, data_format
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    the optional attributes of the isPartOf property.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    core_data.pop("isPartOf", None)
    core_data["isPartOf"] = [data_format]

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    assert core_model_instance.isPartOf[0].type == data_format["@type"]
    assert core_model_instance.isPartOf[0].name == data_format["name"]
    if "description" in data_format:
        assert core_model_instance.isPartOf[
            0].description == data_format["description"]
    if "url" in data_format:
        assert core_model_instance.isPartOf[
            0].url == HttpUrl(data_format["url"])


@pytest.mark.parametrize("dt_type", ["datetime", None])
@pytest.mark.asyncio
async def test_core_schema_date_value_type(core_data, core_model, dt_type):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    allowed value types for the date type attributes (dateCreated, dateModified, and datePublished).
    Also testing that dateModified and datePublished are optional.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    # TODO: test 'date' type after knowing whether we need to support both
    # date and datetime
    if dt_type == "date":
        core_data["dateCreated"] = "2020-01-01"
        core_data["dateModified"] = "2020-02-01"
        core_data["datePublished"] = "2020-05-01"
    elif dt_type == "datetime":
        core_data["dateCreated"] = "2020-01-01T10:00:05"
        core_data["dateModified"] = "2020-02-01T11:20:30"
        core_data["datePublished"] = "2020-05-01T08:00:45"
    else:
        core_data["dateCreated"] = "2020-01-01T10:00:05"
        core_data.pop("dateModified", None)
        core_data.pop("datePublished", None)

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    if dt_type == "date":
        assert core_model_instance.dateCreated == datetime.date(2020, 1, 1)
        assert core_model_instance.dateModified == datetime.date(2020, 2, 1)
        assert core_model_instance.datePublished == datetime.date(2020, 5, 1)
    elif dt_type == "datetime":
        assert core_model_instance.dateCreated == datetime.datetime(
            2020, 1, 1, 10, 0, 5
        )
        assert core_model_instance.dateModified == datetime.datetime(
            2020, 2, 1, 11, 20, 30
        )
        assert core_model_instance.datePublished == datetime.datetime(
            2020, 5, 1, 8, 0, 45
        )
    else:
        assert core_model_instance.dateCreated == datetime.datetime(
            2020, 1, 1, 10, 0, 5
        )
        assert core_model_instance.dateModified is None
        assert core_model_instance.datePublished is None


@pytest.mark.parametrize("provider_type", ["person", "organization"])
@pytest.mark.asyncio
async def test_core_schema_provider_value_type(core_data, core_model, provider_type):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    allowed value types for the provider.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    core_data.pop("provider", None)
    if provider_type == "person":
        core_data["provider"] = {
            "@type": "Person",
            "name": "John Doe",
            "email": "jdoe@gmail.com",
        }
    else:
        core_data["provider"] = {
            "@type": "Organization",
            "name": "HydroShare",
            "url": "https://hydroshare.org",
        }

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    provider = core_model_instance.provider
    if provider_type == "person":
        assert provider.type == "Person"
        assert provider.name == "John Doe"
        assert provider.email == "jdoe@gmail.com"
    else:
        assert provider.type == "Organization"
        assert provider.name == "HydroShare"
        assert provider.url == HttpUrl("https://hydroshare.org")


@pytest.mark.parametrize("multiple_values", [True, False, None])
@pytest.mark.asyncio
async def test_core_schema_subject_of_cardinality(
    core_data, core_model, multiple_values
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    that the subjectOf property is optional and one or more values can be added for this property.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    if multiple_values is None:
        core_data.pop("subjectOf", None)
    elif multiple_values:
        core_data["subjectOf"] = [
            {
                "@type": "CreativeWork",
                "name": "Test subject of - 1",
                "url": "https://www.hydroshare.org/hsapi/resource/c1be74eeea614d65a29a185a66a7552f/scimeta/",
                "description": "Test description - 1",
            },
            {
                "@type": "CreativeWork",
                "name": "Test subject of - 2",
                "description": "Test description - 2",
            },
        ]
    else:
        core_data["subjectOf"] = [
            {"@type": "CreativeWork", "name": "Test subject of"}]

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    if multiple_values and multiple_values is not None:
        assert len(core_model_instance.subjectOf) == 2
        assert core_model_instance.subjectOf[0].type == "CreativeWork"
        assert core_model_instance.subjectOf[0].name == "Test subject of - 1"
        assert core_model_instance.subjectOf[0].url == HttpUrl(
            "https://www.hydroshare.org/hsapi/resource/c1be74eeea614d65a29a185a66a7552f/scimeta/"
        )
        assert core_model_instance.subjectOf[
            0].description == "Test description - 1"

        assert core_model_instance.subjectOf[1].type == "CreativeWork"
        assert core_model_instance.subjectOf[1].name == "Test subject of - 2"
        assert core_model_instance.subjectOf[
            1].description == "Test description - 2"
    elif multiple_values is not None:
        assert len(core_model_instance.subjectOf) == 1
        assert core_model_instance.subjectOf[0].type == "CreativeWork"
        assert core_model_instance.subjectOf[0].name == "Test subject of"
    else:
        assert core_model_instance.subjectOf is None


@pytest.mark.parametrize("include_version", [True, False])
@pytest.mark.asyncio
async def test_core_schema_version_cardinality(core_data, core_model, include_version):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    that the version property is optional.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    if include_version:
        core_data["version"] = "v1.0"
    else:
        core_data.pop("version", None)

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    if include_version:
        assert core_model_instance.version == "v1.0"
    else:
        assert core_model_instance.version is None


@pytest.mark.parametrize("include_language", [True, False])
@pytest.mark.asyncio
async def test_core_schema_language_cardinality(
    core_data, core_model, include_language
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    that the inLanguage property is optional.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    if include_language:
        core_data["inLanguage"] = "eng"
    else:
        core_data.pop("inLanguage", None)

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    if include_language:
        assert core_model_instance.inLanguage == "eng"
    else:
        assert core_model_instance.inLanguage is None


@pytest.mark.parametrize("multiple_funding", [True, False, None])
@pytest.mark.asyncio
async def test_core_schema_funding_cardinality(core_data, core_model, multiple_funding):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    that the funding property is optional and one or more values can be added to this property.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model

    if multiple_funding and multiple_funding is not None:
        core_data["funding"] = [
            {
                "@type": "Grant",
                "name": "HDR Institute: Geospatial Understanding through an Integrative Discovery Environment - 1",
                "identifier": "https://nsf.gov/awardsearch/showAward?AWD_ID=2118329",
            },
            {
                "@type": "Grant",
                "name": "HDR Institute: Geospatial Understanding through an Integrative Discovery Environment - 2",
                "description": "Test grant description",
            },
        ]
    elif multiple_funding is not None:
        core_data["funding"] = [
            {
                "@type": "Grant",
                "name": "HDR Institute: Geospatial Understanding through an Integrative Discovery Environment",
                "identifier": "https://nsf.gov/awardsearch/showAward?AWD_ID=2118329",
                "description": "Test grant description",
            }
        ]
    else:
        core_data.pop("funding", None)

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    if multiple_funding and multiple_funding is not None:
        assert core_model_instance.funding[0].type == "Grant"
        assert (
            core_model_instance.funding[0].name
            == "HDR Institute: Geospatial Understanding through an Integrative Discovery Environment - 1"
        )
        assert (
            core_model_instance.funding[0].identifier
            == "https://nsf.gov/awardsearch/showAward?AWD_ID=2118329"
        )
        # assert core_model_instance.funding[0].funder.type == "Organization"
        # assert core_model_instance.funding[0].funder.name == "National Science Foundation"
        # assert core_model_instance.funding[0].funder.url[0] == "https://ror.org/021nxhr62"
        # assert core_model_instance.funding[0].funder.identifier[1] == "https://doi.org/10.13039/100000001"
        assert core_model_instance.funding[1].type == "Grant"
        assert (
            core_model_instance.funding[1].name
            == "HDR Institute: Geospatial Understanding through an Integrative Discovery Environment - 2"
        )
        assert core_model_instance.funding[
            1].description == "Test grant description"
        # assert core_model_instance.funding[1].funder.type == "Person"
        # assert core_model_instance.funding[1].funder.name == "John Doe"
        # assert core_model_instance.funding[1].funder.email == "johnd@gmail.com"
    elif multiple_funding is not None:
        assert core_model_instance.funding[0].type == "Grant"
        assert (
            core_model_instance.funding[0].name
            == "HDR Institute: Geospatial Understanding through an Integrative Discovery Environment"
        )
        assert (
            core_model_instance.funding[0].identifier
            == "https://nsf.gov/awardsearch/showAward?AWD_ID=2118329"
        )
        assert core_model_instance.funding[
            0].description == "Test grant description"
        # assert core_model_instance.funding[0].funder.type == "Person"
        # assert core_model_instance.funding[0].funder.name == "John Doe"
        # assert core_model_instance.funding[0].funder.email == "johnd@gmail.com"
    else:
        assert core_model_instance.funding is None


@pytest.mark.parametrize("include_funder", [True, False])
@pytest.mark.asyncio
async def test_core_schema_funding_funder_optional(
    core_data, core_model, include_funder
):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    value for the funder attribute of the funding property is optional.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    core_data.pop("funding", None)
    if include_funder:
        core_data["funding"] = [
            {
                "@type": "Grant",
                "name": "HDR Institute: Geospatial Understanding through an Integrative Discovery Environment",
                "identifier": "https://nsf.gov/awardsearch/showAward?AWD_ID=2118329",
                "description": "Test grant description - 1",
                "funder": {
                    "@type": "Organization",
                    "name": "National Science Foundation",
                    "url": "https://www.nsf.gov",
                },
            },
            {
                "@type": "Grant",
                "name": "Collaborative Research: Network Hub: Enabling, Supporting, and Communicating Critical Zone Research.",
                "identifier": "NSF AWARD 2012748",
                "description": "Test grant description - 2",
                "funder": {
                    "@type": "Organization",
                    "name": "National Science Foundation",
                    "address": "2415 Eisenhower Avenue Alexandria, Virginia 22314",
                },
            },
            {
                "@type": "Grant",
                "name": "HDR Institute: Geospatial Understanding through an Integrative Discovery Environment - 3",
                "identifier": "https://usda.gov/awardsearch/showAward?AWD_ID=2118330",
                "description": "Test grant description - 3",
                "funder": {"@type": "Organization", "name": "USDA"},
            },
        ]
    else:
        core_data["funding"] = [
            {
                "@type": "Grant",
                "name": "HDR Institute: Geospatial Understanding through an Integrative Discovery Environment",
                "identifier": "https://nsf.gov/awardsearch/showAward?AWD_ID=2118329",
                "description": "Test grant description - 1",
            }
        ]

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)

    if include_funder:
        assert core_model_instance.funding[0].funder.type == "Organization"
        assert (
            core_model_instance.funding[
                0].funder.name == "National Science Foundation"
        )
        assert core_model_instance.funding[0].funder.url == HttpUrl(
            "https://www.nsf.gov"
        )
        assert core_model_instance.funding[1].funder.type == "Organization"
        assert (
            core_model_instance.funding[
                1].funder.name == "National Science Foundation"
        )
        assert (
            core_model_instance.funding[1].funder.address
            == "2415 Eisenhower Avenue Alexandria, Virginia 22314"
        )
        assert core_model_instance.funding[2].funder.type == "Organization"
        assert core_model_instance.funding[2].funder.name == "USDA"
    else:
        assert core_model_instance.funding[0].funder is None


@pytest.mark.parametrize("include_citation", [True, False])
@pytest.mark.asyncio
async def test_core_schema_citation_optional(core_data, core_model, include_citation):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    citation is optional for the funding property.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    core_data.pop("citation", None)
    if include_citation:
        core_data["citation"] = ["Test citation"]

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    if include_citation:
        assert core_model_instance.citation == ["Test citation"]
    else:
        assert core_model_instance.citation is None


@pytest.mark.parametrize("include_publisher", [True, False])
@pytest.mark.asyncio
async def test_core_schema_publisher_optional(core_data, core_model, include_publisher):
    """Test that a core metadata pydantic model can be created from core metadata json.
    Purpose of the test is to validate core metadata schema as defined by the pydantic model where we are testing
    publisher is optional for the funding property.
    Note: This test does nat add a record to the database.
    """
    core_data = core_data
    core_model = core_model
    core_data.pop("publisher", None)
    if include_publisher:
        core_data["publisher"] = {
            "@type": "Organization",
            "name": "HydroShare",
            "url": "https://hydroshare.org",
            "address": "1167 Massachusetts Ave Suites 418 & 419, Arlington, MA 02476",
        }

    # validate the data model
    core_model_instance = await utils.validate_data_model(core_data, core_model)
    if include_publisher:
        assert core_model_instance.publisher.type == "Organization"
        assert core_model_instance.publisher.name == "HydroShare"
        assert core_model_instance.publisher.url == HttpUrl(
            "https://hydroshare.org")
        assert (
            core_model_instance.publisher.address
            == "1167 Massachusetts Ave Suites 418 & 419, Arlington, MA 02476"
        )
    else:
        assert core_model_instance.publisher is None
