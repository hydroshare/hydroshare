import re
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, Union, Literal


from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    AnyUrl,
    field_validator,
    model_validator,
    GetJsonSchemaHandler,
    ValidationInfo,
)


from pydantic.json_schema import JsonSchemaValue

orcid_pattern = "\\b\\d{4}-\\d{4}-\\d{4}-\\d{3}[0-9X]\\b"
orcid_pattern_placeholder = "e.g. '0000-0001-2345-6789'"
orcid_pattern_error = "must match the ORCID pattern. e.g. '0000-0001-2345-6789'"


def modify_json_schema(schema: dict[str, Any]) -> None:
    for prop in schema.get("properties", {}).values():
        if "format" in prop and prop["format"] == "uri":
            # Replace "format" with a regex pattern for URL matching
            prop.pop("format")
            prop["pattern"] = (
                "^(http:\\/\\/www\\.|https:\\/\\/www\\.|http:\\/\\/|https:\\/\\/)?"
                "[a-z0-9]+([\\-\\.]{1}[a-z0-9]+)*\\.[a-z]{2,5}(:[0-9]{1,5})?"
                "(\\/.*)?$"
            )
            prop["errorMessage"] = {"pattern": 'must match format "url"'}


class SchemaBaseModel(BaseModel):
    model_config = ConfigDict(json_schema_extra=modify_json_schema, extra="allow")


class DefinedTerm(SchemaBaseModel):
    type: str = Field(alias="@type", default="DefinedTerm")
    name: str = Field(description="The name of the term or item being defined.")
    description: str = Field(description="The description of the item being defined.")


class Published(DefinedTerm):
    name: str = Field(default="Published")
    description: str = Field(
        default="The resource has been permanently published and should be considered final and complete",
        readOnly=True,
        description="The description of the item being defined.",
    )


class Public(DefinedTerm):
    name: str = Field(default="Public")
    description: str = Field(
        default="The resource is publicly accessible and can be viewed or downloaded by anyone",
        readOnly=True,
        description="The description of the item being defined.",
    )


class Private(DefinedTerm):
    name: str = Field(default="Private")
    description: str = Field(
        default="The resource is private and can only be accessed by authorized users",
        readOnly=True,
        description="The description of the item being defined.",
    )


class Discoverable(DefinedTerm):
    name: str = Field(default="Discoverable")
    description: str = Field(
        default="The resource is discoverable and can be found through search engines or other discovery mechanisms",
        readOnly=True,
        description="The description of the item being defined.",
    )


class CreativeWork(SchemaBaseModel):
    type: Literal["CreativeWork"] = Field(
        alias="@type",  # type: ignore
        default="CreativeWork",
        description="Submission type can include various forms of content, such as datasets, "
        "software source code, digital documents, etc.",
    )
    name: str = Field(description="Submission's name or title", title="Name or title")
    description: Optional[str] = Field(
        description="The description of the creative work.", default=None
    )
    url: Optional[HttpUrl] = Field(
        title="URL",
        description="A URL to the creative work.",
        default=None,
    )


class Person(SchemaBaseModel):
    type: Literal["Person"] = Field(
        alias="@type", description="A person.", default="Person"  # type: ignore
    )
    name: str = Field(
        description="A string containing the full name of the person. Personal name format: Family Name, Given Name."
    )
    email: Optional[EmailStr] = Field(
        description="A string containing an email address for the person.", default=None
    )
    identifier: Optional[List[str]] = Field(
        description="Unique identifiers for the person. Where identifiers can be encoded as URLs, enter URLs here.",
        default=None,
    )
    model_config = {
        "populate_by_name": True,  # Ensures aliases work during model initialization
    }


class Organization(SchemaBaseModel):
    type: Literal["Organization"] = Field(
        alias="@type",  # type: ignore
        default="Organization",
    )
    name: str = Field(description="Name of the provider organization or repository.")
    url: Optional[HttpUrl] = Field(
        title="URL",
        description="A URL to the homepage for the organization.",
        default=None,
    )
    address: Optional[str] = Field(
        description="Full address for the organization - e.g., “8200 Old Main Hill, Logan, UT 84322-8200”.",
        default=None,
    )  # Should address be a string or another constrained type?
    model_config = {
        "populate_by_name": True,  # Ensures aliases work during model initialization
    }


class Affiliation(Organization):
    name: str = Field(
        description="Name of the organization the creator is affiliated with."
    )


class Provider(Person):
    identifier: Optional[str] = Field(
        description="ORCID identifier for the person.",
        json_schema_extra={
            "pattern": orcid_pattern,
            "options": {"placeholder": orcid_pattern_placeholder},
            "errorMessage": {"pattern": orcid_pattern_error},
        },
        default=None,
    )
    email: Optional[EmailStr] = Field(
        description="A string containing an email address for the provider.",
        default=None,
    )
    affiliation: Optional[Affiliation] = Field(
        description="The affiliation of the creator with the organization.",
        default=None,
    )


class Creator(Person):
    identifier: Optional[str] = Field(
        description="ORCID identifier for creator.",
        json_schema_extra={
            "pattern": orcid_pattern,
            "options": {"placeholder": orcid_pattern_placeholder},
            "errorMessage": {"pattern": orcid_pattern_error},
        },
        default=None,
    )
    email: Optional[EmailStr] = Field(
        description="A string containing an email address for the creator.",
        default=None,
    )
    affiliation: Optional[Affiliation] = Field(
        description="The affiliation of the creator with the organization.",
        default=None,
    )


class Contributor(Person):
    identifier: Optional[str] = Field(
        description="ORCID identifier for contributor.",
        json_schema_extra={
            "pattern": orcid_pattern,
            "options": {"placeholder": orcid_pattern_placeholder},
            "errorMessage": {"pattern": orcid_pattern_error},
        },
        default=None,
    )
    email: Optional[EmailStr] = Field(
        description="A string containing an email address for the creator.",
        default=None,
    )
    affiliation: Optional[Affiliation] = Field(
        description="The affiliation of the creator with the organization.",
        default=None,
    )


class FunderOrganization(Organization):
    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: JsonSchemaValue, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        schema.update(schema, title="Funding Organization")
        return schema

    name: str = Field(description="Name of the organization.")


class PublisherOrganization(Organization):
    name: str = Field(description="Name of the publishing organization.")
    url: Optional[HttpUrl] = Field(
        title="URL",
        description="A URL to the homepage for the publisher organization or repository.",
        default=None,
    )


class SourceOrganization(Organization):
    name: str = Field(description="Name of the organization that created the data.")


class DefinedTerm(SchemaBaseModel):
    type: Literal["DefinedTerm"] = Field(alias="@type", default="DefinedTerm")  # type: ignore
    name: str = Field(description="The name of the term or item being defined.")
    description: str = Field(description="The description of the item being defined.")


class Draft(DefinedTerm):
    name: str = Field(default="Draft")
    description: str = Field(
        default="The resource is in draft state and should not be considered final. Content and metadata may change",
        description="The description of the item being defined.",
        json_schema_extra={"readOnly": True},
    )


class Incomplete(DefinedTerm):
    name: str = Field(default="Incomplete")
    description: str = Field(
        default="Data collection is ongoing or the resource is not completed",
        description="The description of the item being defined.",
        json_schema_extra={"readOnly": True},
    )


class Obsolete(DefinedTerm):
    name: str = Field(default="Obsolete")
    description: str = Field(
        default="The resource has been replaced by a newer version, or the resource is no longer considered applicable",
        description="The description of the item being defined.",
        json_schema_extra={"readOnly": True},
    )


class Published(DefinedTerm):
    name: str = Field(default="Published")
    description: str = Field(
        default="The resource has been permanently published and should be considered final and complete",
        description="The description of the item being defined.",
        json_schema_extra={"readOnly": True},
    )


class HasPart(CreativeWork):
    url: Optional[HttpUrl] = Field(
        title="URL", description="The URL address to the data resource.", default=None
    )
    description: Optional[str] = Field(
        description="Information about a related resource that is part of this resource.",
        default=None,
    )


class IsPartOf(CreativeWork):
    url: Optional[HttpUrl] = Field(
        title="URL", description="The URL address to the data resource.", default=None
    )
    description: Optional[str] = Field(
        description="Information about a related resource that this resource is a "
        "part of - e.g., a related collection.",
        default=None,
    )


class MediaObjectPartOf(CreativeWork):
    url: Optional[HttpUrl] = Field(
        title="URL",
        description="The URL address to the related metadata document.",
        default=None,
    )
    description: Optional[str] = Field(
        description="Information about a related metadata document.", default=None
    )


class SubjectOf(CreativeWork):
    url: Optional[HttpUrl] = Field(
        title="URL",
        description="The URL address that serves as a reference to access additional details related to the record. "
        "It is important to note that this type of metadata solely pertains to the record itself and "
        "may not necessarily be an integral component of the record, unlike the HasPart metadata.",
        default=None,
    )
    description: Optional[str] = Field(
        description="Information about a related resource that is about or describes this "
        "resource - e.g., a related metadata document describing the resource.",
        default=None,
    )


class LanguageEnum(str, Enum):
    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: JsonSchemaValue, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        schema.update(type="string", title="Language", description="")
        return schema

    eng = "eng"
    esp = "esp"


class InLanguageStr(str):
    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: JsonSchemaValue, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        schema.update(
            type="string", title="Other", description="Please specify another language."
        )
        return schema


# TODO: should we allow a list of identifiers? Does this align with SchemaOrg?
# Doing so means that we are actually storing this as a comma separated string
# of identifiers which seems strange.
class IdentifierStr(str):
    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: JsonSchemaValue, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        schema.update(
            {"type": "array", "items": {"type": "string", "title": "Identifier"}}
        )
        return schema

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(
        cls, value: Union[str, List[str]], info: ValidationInfo
    ) -> "IdentifierStr":
        if isinstance(value, str):
            value = [value]  # Convert single string to list
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise TypeError("Identifier must be a string or a list of strings")
        return cls(", ".join(value))  # Join the list into a single string for storage


# TODO: start here.
class SpatialReference(SchemaBaseModel):
    type: Literal["SpatialReference"] = Field(
        alias="@type",  # type: ignore
        default="SpatialReference",
        description="The spatial reference system associated with the Place's geographic representation.",
    )
    name: str = Field(
        title="Name",
        description="Name of the spatial reference system.",
    )
    srsType: str = Field(
        title="SRS Type",
        description="Type of the spatial reference system, either Geographic or Projected.",
    )
    code: Optional[str] = Field(
        title="Code",
        description="Code of the spatial reference system.",
        default=None,
    )
    wktString: Optional[str] = Field(
        title="SRS WKT String",
        description="The string representation of the spatial reference system in Well-Known-Text format.",
        default=None,
    )

    @field_validator("srsType")
    def validate_content_size(cls, v):
        v = v.strip().lower()
        if not v:
            raise ValueError("empty string")
        if v not in ["geographic", "projected"]:
            raise ValueError("SRS Type must be either 'geographic' or 'projected'")
        return v


class Grant(SchemaBaseModel):
    type: Literal["Grant"] = Field(
        alias="@type",  # type: ignore
        default="Grant",
        description="This metadata represents details about a grant or financial assistance provided to an "
        "individual(s) or organization(s) for supporting the work related to the record.",
    )
    name: str = Field(
        title="Name or title",
        description="A text string indicating the name or title of the grant or financial assistance.",
    )
    description: Optional[str] = Field(
        description="A text string describing the grant or financial assistance.",
        default=None,
    )
    identifier: Optional[str] = Field(
        title="Funding identifier",
        description="Grant award number or other identifier.",
        default=None,
    )
    funder: Optional[FunderOrganization] = Field(
        description="The organization that provided the funding or sponsorship.",
        default=None,
    )


class TemporalCoverage(SchemaBaseModel):
    startDate: datetime = Field(
        title="Start date",
        description="A date/time object containing the instant corresponding to the commencement of the time "
        "interval (ISO8601 formatted date - YYYY-MM-DDTHH:MM).",
        json_schema_extra={
            "formatMaximum": {"$data": "1/endDate"},
            "errorMessage": {
                "formatMaximum": "must be lesser than or equal to End date"
            },
        },
    )
    endDate: Optional[datetime] = Field(
        title="End date",
        description="A date/time object containing the instant corresponding to the termination of the time "
        "interval (ISO8601 formatted date - YYYY-MM-DDTHH:MM). If the ending date is left off, "
        "that means the temporal coverage is ongoing.",
        json_schema_extra={
            "formatMinimum": {"$data": "1/startDate"},
            "errorMessage": {
                "formatMinimum": "must be greater than or equal to Start date"
            },
        },
        default=None,
    )


class GeoCoordinates(SchemaBaseModel):
    type: Literal["GeoCoordinates"] = Field(
        alias="@type",  # type: ignore
        default="GeoCoordinates",
        description="Geographic coordinates that represent a specific location on the Earth's surface. "
        "GeoCoordinates typically consists of two components: latitude and longitude.",
    )
    latitude: float = Field(
        description="Represents the angular distance of a location north or south of the equator, "
        "measured in degrees and ranges from -90 to +90 degrees."
    )
    longitude: float = Field(
        description="Represents the angular distance of a location east or west of the Prime Meridian, "
        "measured in degrees and ranges from -180 to +180 degrees."
    )

    @field_validator("latitude")
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class GeoShape(SchemaBaseModel):
    type: Literal["GeoShape"] = Field(
        alias="@type",  # type: ignore
        default="GeoShape",
        description="A structured representation that describes the coordinates of a geographic feature.",
    )
    validate_bbox: bool = Field(
        default=True,
        exclude=True,
        description="Flag to turn on/off bounding box validation",
    )
    box: str = Field(
        description="A box is a rectangular region defined by a pair of coordinates representing the "
        "southwest and northeast corners of the box."
    )

    @field_validator("box")
    def validate_box(cls, v, info):
        return v
        # ignoring validation for now
        if not isinstance(v, str):
            raise TypeError("string required")
        v = v.strip()
        if not v:
            raise ValueError("empty string")

        # exit if validation is turned off
        if not info.data.get("validate_bbox", 'Could not find "validate_bbox"'):
            return v

        v_parts = v.split(" ")
        if len(v_parts) != 4:
            raise ValueError("Bounding box must have 4 coordinate points")
        for index, item in enumerate(v_parts, start=1):
            try:
                item = float(item)
            except ValueError:
                raise ValueError("Bounding box coordinate value is not a number")
            item = abs(item)
            if index % 2 == 0:
                if item > 180:
                    raise ValueError(
                        "Bounding box coordinate east/west must be between -180 and 180"
                    )
            elif item > 90:
                raise ValueError(
                    "Bounding box coordinate north/south must be between -90 and 90"
                )

        return v


class PropertyValue(SchemaBaseModel):
    type: Literal["PropertyValue"] = Field(
        alias="@type",  # type: ignore
        default="PropertyValue",
        description="A property-value pair.",
    )
    name: str = Field(description="The name of the property.")

    value: Union[str, float, bool] = (
        Field(  # this also could be a StructuredValue for more complex cases (if we want)
            description="The value of the property."
        )
    )

    propertyID: Optional[str] = Field(
        title="Property ID", description="The ID of the property.", default=None
    )
    unitCode: Optional[str] = Field(
        title="Measurement unit",
        description="The unit of measurement for the value.",
        default=None,
    )
    description: Optional[str] = Field(
        description="A description of the property.", default=None
    )
    minValue: Optional[float] = Field(
        title="Minimum value",
        description="The minimum allowed value for the property.",
        default=None,
    )
    maxValue: Optional[float] = Field(
        title="Maximum value",
        description="The maximum allowed value for the property.",
        default=None,
    )
    measurementTechnique: Optional[str] = Field(
        title="Measurement technique",
        description="A technique or technology used in a measurement.",
        default=None,
    )
    model_config = {
        "populate_by_name": True,  # Ensures aliases work during model initialization
        "title": "PropertyValue",
    }


class Place(SchemaBaseModel):
    type: Literal["Place"] = Field(
        alias="@type",  # type: ignore
        default="Place",
        description="Represents the focus area of the record's content.",
    )
    name: Optional[str] = Field(description="Name of the place.", default=None)
    geo: Optional[Union[GeoCoordinates, GeoShape]] = Field(
        description="Specifies the geographic coordinates of the place in the form of a point location, line, "
        "or area coverage extent.",
        default=None,
    )

    additionalProperty: Optional[List[PropertyValue]] = Field(
        title="Additional properties",
        default=None,
        description="Additional properties of the place.",
    )

    srs: Optional[SpatialReference] = Field(
        description="The spatial reference system associated with the Place's geographic representation",
        default=None,
    )

    @model_validator(mode="after")
    def validate_geo_or_name_required(self):
        if not self.name and not self.geo:
            raise ValueError(
                "Either place name or geo location of the place must be provided"
            )
        return self


class MediaObject(SchemaBaseModel):
    type: Literal["MediaObject"] = Field(
        alias="@type",  # type: ignore
        default="MediaObject",
        description="An item that encodes the record.",
    )
    contentUrl: Union[str, AnyUrl] = Field(
        title="Content URL",
        description="The direct URL link to access or download the actual content of the media object.",
    )
    encodingFormat: Optional[str] = Field(
        title="Encoding format",
        description="Represents the specific file format in which the media is encoded.",
        default=None,
    )  # TODO enum for encoding formats
    contentSize: str = Field(
        title="Content size",
        description="Represents the file size, expressed in bytes, kilobytes, megabytes, or another "
        "unit of measurement.",
    )
    name: str = Field(description="The name of the media object (file).")
    sha256: Optional[str] = Field(
        title="SHA-256",
        description="The SHA-256 hash of the media object.",
        default=None,
    )
    isPartOf: Optional[List[MediaObjectPartOf]] = Field(
        title="Is part of",
        description="Link to or citation for a related metadata document that this media object is a part of",
        default=None,
    )

    @field_validator("contentSize")
    def validate_content_size(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("empty string")

        match = re.match(r"([0-9.]+)([a-zA-Z]+$)", v.replace(" ", ""))
        if not match:
            raise ValueError("invalid format")

        size_unit = match.group(2)
        if size_unit.upper() not in [
            "KB",
            "MB",
            "GB",
            "TB",
            "PB",
            "KILOBYTES",
            "MEGABYTES",
            "GIGABYTES",
            "TERABYTES",
            "PETABYTES",
        ]:
            raise ValueError("invalid unit")

        return v

    # TODO: not validating the SHA-256 hash for now as the hydroshare content file hash is in md5 format
    # @validator('sha256')
    # def validate_sha256_string_format(cls, v):
    #     if v:
    #         v = v.strip()
    #         if v and not re.match(r"^[a-fA-F0-9]{64}$", v):
    #             raise ValueError('invalid SHA-2


class DataDownload(MediaObject):
    type: Literal["DataDownload"] = Field(
        alias="@type",  # type: ignore
        default="DataDownload",
        description="All or part of a Dataset in downloadable form.",
    )
    measurementMethod: Optional[Union[DefinedTerm, HttpUrl, str]] = Field(
        title="Measurement method",
        description="A subproperty of measurementTechnique that can be used for specifying specific methods, in particular via MeasurementMethodEnum.",
        default=None,
    )
    measurementTechnique: Optional[Union[DefinedTerm, HttpUrl, str]] = Field(
        title="Measurement technique",
        description="A technique, method or technology used in an Observation, StatisticalVariable or Dataset (or DataDownload, DataCatalog), corresponding to the method used for measuring the corresponding variable(s) (for datasets, described using variableMeasured; for Observation, a StatisticalVariable). Often but not necessarily each variableMeasured will have an explicit representation as (or mapping to) an property such as those defined in Schema.org, or other RDF vocabularies and 'knowledge graphs'. In that case the subproperty of variableMeasured called measuredProperty is applicable.",
        default=None,
    )


class VideoObject(MediaObject):
    type: Literal["VideoObject"] = Field(
        alias="@type",  # type: ignore
        default="VideoObject",
        description="A video file.",
    )
    # there are many fields that we could implement here, but I don't think they'll be
    # used. I'm adding VideoObject because it's referenced in out unit tests. Consider
    # removing in the future.


# combine the media objects together to make referencing easier
MediaType = Union[MediaObject, DataDownload, VideoObject]


class Dataset(CreativeWork):
    measurementMethod: Optional[
        Union[
            HttpUrl,
            List[HttpUrl],
            DefinedTerm,
            List[DefinedTerm],
            str,
            List[str],
        ]
    ] = None
    issn: Optional[Union[str, List[str]]] = None
    measurementTechnique: Optional[
        Union[
            str,
            List[str],
            HttpUrl,
            List[HttpUrl],
            DefinedTerm,
            List[DefinedTerm],
        ]
    ] = None
    catalog: Optional[Union["DataCatalog", List["DataCatalog"]]] = None
    variablesMeasured: Optional[
        Union[str, List[str], "PropertyValue", List["PropertyValue"]]
    ] = None
    variableMeasured: Optional[
        Union[
            str,
            List[str],
            "PropertyValue",
            List["PropertyValue"],
        ]
    ] = None
    includedDataCatalog: Optional[Union["DataCatalog", List["DataCatalog"]]] = None
    includedInDataCatalog: Optional[Union["DataCatalog", List["DataCatalog"]]] = None
    datasetTimeInterval: Optional[Union[datetime, List[datetime]]] = None
    distribution: Optional[Union["DataDownload", List["DataDownload"]]] = None


class DataCatalog(CreativeWork):
    """
    A collection of datasets.
    """

    measurementMethod: Optional[
        Union[
            HttpUrl,
            List[HttpUrl],
            DefinedTerm,
            List[DefinedTerm],
            str,
            List[str],
        ]
    ] = None
    dataset: Optional[Union[Dataset, List[Dataset]]] = None
    measurementTechnique: Optional[
        Union[
            str,
            List[str],
            HttpUrl,
            List[HttpUrl],
            DefinedTerm,
            List[DefinedTerm],
        ]
    ] = None
