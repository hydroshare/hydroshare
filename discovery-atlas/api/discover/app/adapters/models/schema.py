import json
import re
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, EmailStr, Field, GetJsonSchemaHandler, HttpUrl, root_validator, validator
from pydantic_core import CoreSchema
from typing_extensions import Literal

orcid_pattern = "\\b\\d{4}-\\d{4}-\\d{4}-\\d{3}[0-9X]\\b"
orcid_pattern_placeholder = "e.g. '0000-0001-2345-6789'"
orcid_pattern_error = "must match the ORCID pattern. e.g. '0000-0001-2345-6789'"


class SchemaBaseModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True

        @staticmethod
        def json_schema_extra(schema: Dict[str, Any], model) -> None:
            # json schema modification for jsonforms
            for prop in schema.get('properties', {}).values():
                if 'format' in prop and prop['format'] == 'uri':
                    # using a regex for url matching
                    prop.pop('format')
                    prop['pattern'] = (
                        "^(http:\\/\\/www\\.|https:\\/\\/www\\.|http:\\/\\/|https:\\/\\/)?[a-z0-9]+([\\-\\.]{1}[a-z0-9]+)*\\.[a-z]{2,5}(:[0-9]{1,5})?(\\/.*)?$"
                    )
                    prop['errorMessage'] = {"pattern": "must match format \"url\""}


class CreativeWork(SchemaBaseModel):
    type: str = Field(
        alias="@type",
        default="CreativeWork",
        description="Submission type can include various forms of content, such as datasets, "
        "software source code, digital documents, etc.",
    )
    name: str = Field(description="Submission's name or title", title="Name or title")


class Person(SchemaBaseModel):
    type: Literal["Person"] = Field(alias="@type", description="A person.")
    name: str = Field(
        description="A string containing the full name of the person. Personal name format: Family Name, Given Name."
    )
    email: Optional[EmailStr] = Field(description="A string containing an email address for the person.")
    identifier: Optional[List[str]] = Field(
        description="Unique identifiers for the person. Where identifiers can be encoded as URLs, enter URLs here."
    )


class Organization(SchemaBaseModel):
    type: Literal["Organization"] = Field(alias="@type")
    name: str = Field(description="Name of the provider organization or repository.")
    url: Optional[HttpUrl] = Field(title="URL", description="A URL to the homepage for the organization.")
    address: Optional[str] = Field(
        description="Full address for the organization - e.g., “8200 Old Main Hill, Logan, UT 84322-8200”."
    )  # Should address be a string or another constrained type?


class Affiliation(Organization):
    name: str = Field(description="Name of the organization the creator is affiliated with.")


class Provider(Person):
    identifier: Optional[str] = Field(
        description="ORCID identifier for the person.",
        pattern=orcid_pattern,
        options={"placeholder": orcid_pattern_placeholder},
        errorMessage={"pattern": orcid_pattern_error},
    )
    email: Optional[EmailStr] = Field(description="A string containing an email address for the provider.")
    affiliation: Optional[Affiliation] = Field(description="The affiliation of the creator with the organization.")


class Creator(Person):
    identifier: Optional[str] = Field(
        description="ORCID identifier for creator.",
        pattern=orcid_pattern,
        options={"placeholder": orcid_pattern_placeholder},
        errorMessage={"pattern": orcid_pattern_error},
    )
    email: Optional[EmailStr] = Field(description="A string containing an email address for the creator.")
    affiliation: Optional[Affiliation] = Field(description="The affiliation of the creator with the organization.")


class FunderOrganization(Organization):
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> Dict[str, Any]:
        json_schema = super().__get_pydantic_json_schema__(core_schema, handler)
        json_schema = handler.resolve_ref_schema(json_schema)
        schema = json.loads(FunderOrganization.schema_json())
        json_schema.update(schema, title="Funding Organization")
        return json_schema

    name: str = Field(description="Name of the organization.")


class PublisherOrganization(Organization):
    name: str = Field(description="Name of the publishing organization.")
    url: Optional[HttpUrl] = Field(
        title="URL", description="A URL to the homepage for the publisher organization or repository."
    )


class DefinedTerm(SchemaBaseModel):
    type: str = Field(alias="@type", default="DefinedTerm")
    name: str = Field(description="The name of the term or item being defined.")
    description: str = Field(description="The description of the item being defined.")


class Draft(DefinedTerm):
    name: str = Field(default="Draft")
    description: str = Field(
        default="The resource is in draft state and should not be considered final. Content and metadata may change",
        readOnly=True,
        description="The description of the item being defined.",
    )


class Incomplete(DefinedTerm):
    name: str = Field(default="Incomplete")
    description: str = Field(
        default="Data collection is ongoing or the resource is not completed",
        readOnly=True,
        description="The description of the item being defined.",
    )


class Obsolete(DefinedTerm):
    name: str = Field(default="Obsolete")
    description: str = Field(
        default="The resource has been replaced by a newer version, or the resource is no longer considered applicable",
        readOnly=True,
        description="The description of the item being defined.",
    )


class Published(DefinedTerm):
    name: str = Field(default="Published")
    description: str = Field(
        default="The resource has been permanently published and should be considered final and complete",
        readOnly=True,
        description="The description of the item being defined.",
    )


class HasPart(CreativeWork):
    url: Optional[HttpUrl] = Field(title="URL", description="The URL address to the data resource.")
    description: Optional[str] = Field(
        description="Information about a related resource that is part of this resource."
    )


class IsPartOf(CreativeWork):
    url: Optional[HttpUrl] = Field(title="URL", description="The URL address to the data resource.")
    description: Optional[str] = Field(
        description="Information about a related resource that this resource is a "
        "part of - e.g., a related collection."
    )


class SubjectOf(CreativeWork):
    url: Optional[HttpUrl] = Field(
        title="URL",
        description="The URL address that serves as a reference to access additional details related to the record. "
        "It is important to note that this type of metadata solely pertains to the record itself and "
        "may not necessarily be an integral component of the record, unlike the HasPart metadata.",
    )
    description: Optional[str] = Field(
        description="Information about a related resource that is about or describes this "
        "resource - e.g., a related metadata document describing the resource."
    )


class License(CreativeWork):
    name: str = Field(
        description="A text string indicating the name of the license under which the resource is shared."
    )
    url: Optional[HttpUrl] = Field(title="URL", description="A URL for a web page that describes the license.")
    description: Optional[str] = Field(
        description="A text string describing the license or containing the text of the license itself."
    )


class LanguageEnum(str, Enum):
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> Dict[str, Any]:
        json_schema = super().__get_pydantic_json_schema__(core_schema, handler)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema.update(type='string', title='Language', description='')
        return json_schema

    eng = 'eng'
    esp = 'esp'


class InLanguageStr(str):
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> Dict[str, Any]:
        json_schema = super().__get_pydantic_json_schema__(core_schema, handler)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema.update(type='string', title='Other', description="Please specify another language.")
        return json_schema


class IdentifierStr(str):
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> Dict[str, Any]:
        json_schema = super().__get_pydantic_json_schema__(core_schema, handler)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema.update(type='string', title='Identifier')
        return json_schema


class Grant(SchemaBaseModel):
    type: str = Field(
        alias="@type",
        default="MonetaryGrant",
        description="This metadata represents details about a grant or financial assistance provided to an "
        "individual(s) or organization(s) for supporting the work related to the record.",
    )
    name: str = Field(
        title="Name or title",
        description="A text string indicating the name or title of the grant or financial assistance.",
    )
    description: Optional[str] = Field(description="A text string describing the grant or financial assistance.")
    identifier: Optional[str] = Field(title="Funding identifier", description="Grant award number or other identifier.")
    funder: Optional[FunderOrganization] = Field(
        description="The organization that provided the funding or sponsorship."
    )


class TemporalCoverage(SchemaBaseModel):
    startDate: datetime = Field(
        title="Start date",
        description="A date/time object containing the instant corresponding to the commencement of the time "
        "interval (ISO8601 formatted date - YYYY-MM-DDTHH:MM).",
        # TODO: these are failing due to a problem with transpiled dependencies inside cznet-vue-core
        # formatMaximum={"$data": "1/endDate"},
        # errorMessage= { "formatMaximum": "must be lesser than or equal to End date" }
    )
    endDate: Optional[datetime] = Field(
        title="End date",
        description="A date/time object containing the instant corresponding to the termination of the time "
        "interval (ISO8601 formatted date - YYYY-MM-DDTHH:MM). If the ending date is left off, "
        "that means the temporal coverage is ongoing.",
        # formatMinimum={"$data": "1/startDate"},
        # errorMessage= { "formatMinimum": "must be greater than or equal to Start date" }
    )


class GeoCoordinates(SchemaBaseModel):
    type: str = Field(
        alias="@type",
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

    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


class GeoShape(SchemaBaseModel):
    type: str = Field(
        alias="@type",
        default="GeoShape",
        description="A structured representation that describes the coordinates of a geographic feature.",
    )
    box: str = Field(
        description="A box is a rectangular region defined by a pair of coordinates representing the "
        "southwest and northeast corners of the box."
    )

    @validator('box')
    def validate_box(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        v = v.strip()
        if not v:
            raise ValueError('empty string')
        v_parts = v.split(' ')
        if len(v_parts) != 4:
            raise ValueError('Bounding box must have 4 coordinate points')
        for index, item in enumerate(v_parts, start=1):
            try:
                item = float(item)
            except ValueError:
                raise ValueError('Bounding box coordinate value is not a number')
            item = abs(item)
            if index % 2 == 0:
                if item > 180:
                    raise ValueError('Bounding box coordinate east/west must be between -180 and 180')
            elif item > 90:
                raise ValueError('Bounding box coordinate north/south must be between -90 and 90')

        return v


class Place(SchemaBaseModel):
    type: str = Field(alias="@type", default="Place", description="Represents the focus area of the record's content.")
    name: Optional[str] = Field(description="Name of the place.")
    geo: Optional[Union[GeoCoordinates, GeoShape]] = Field(
        description="Specifies the geographic coordinates of the place in the form of a point location, line, "
        "or area coverage extent."
    )

    @root_validator(skip_on_failure=True)
    def validate_geo_or_name_required(cls, values):
        name = values.get('name', None)
        geo = values.get('geo', None)
        if not name and not geo:
            raise ValueError('Either place name or geo location of the place must be provided')
        return values


class MediaObject(SchemaBaseModel):
    type: str = Field(alias="@type", default="MediaObject", description="An item that encodes the record.")
    contentUrl: str = Field(
        title="Content URL",
        description="The direct URL link to access or download the actual content of the media object.",
    )
    encodingFormat: str = Field(
        title="Encoding format", description="Represents the specific file format in which the media is encoded."
    )  # TODO enum for encoding formats
    contentSize: str = Field(
        title="Content size",
        description="Represents the file size, expressed in bytes, kilobytes, megabytes, or another "
        "unit of measurement.",
    )
    name: str = Field(description="The name of the media object (file).")
    checksum: str = Field(description="The MD5 checksum of the file")

    @validator('contentSize')
    def validate_content_size(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('empty string')

        match = re.match(r"([0-9.]+)([a-zA-Z]+$)", v.replace(" ", ""))
        if not match:
            raise ValueError('invalid format')

        size_unit = match.group(2)
        if size_unit.upper() not in [
            'KB',
            'MB',
            'GB',
            'TB',
            'PB',
            'KILOBYTES',
            'MEGABYTES',
            'GIGABYTES',
            'TERABYTES',
            'PETABYTES',
        ]:
            raise ValueError('invalid unit')

        return v


class CoreMetadata(SchemaBaseModel):
    context: HttpUrl = Field(
        alias='@context',
        default='https://schema.org',
        description="Specifies the vocabulary employed for understanding the structured data markup.",
    )
    type: str = Field(
        alias="@type",
        title="Submission type",
        default="Dataset",
        description="Submission type can include various forms of content, such as datasets,"
        " software source code, digital documents, etc.",
        enum=["Dataset", "Notebook", "Software Source Code"],
    )
    name: str = Field(
        default=None,
        title="Name or title",
        description="A text string with a descriptive name or title for the resource.",
    )
    description: str = Field(
        default=None,
        title="Description or abstract",
        description="A text string containing a description/abstract for the resource.",
    )
    url: HttpUrl = Field(
        title="URL",
        description="A URL for the landing page that describes the resource and where the content "
        "of the resource can be accessed. If there is no landing page,"
        " provide the URL of the content.",
    )
    identifier: Optional[List[IdentifierStr]] = Field(
        title="Identifiers",
        description="Any kind of identifier for the resource. Identifiers may be DOIs or unique strings "
        "assigned by a repository. Multiple identifiers can be entered. Where identifiers can be "
        "encoded as URLs, enter URLs here.",
    )
    creator: List[Union[Creator, Organization]] = Field(description="Person or Organization that created the resource.")
    dateCreated: datetime = Field(title="Date created", description="The date on which the resource was created.")
    keywords: List[str] = Field(
        min_items=1, description="Keywords or tags used to describe the dataset, delimited by commas."
    )
    license: License = Field(description="A license document that applies to the resource.")
    provider: Union[Organization, Provider] = Field(
        description="The repository, service provider, organization, person, or service performer that provides"
        " access to the resource."
    )
    publisher: Optional[PublisherOrganization] = Field(
        title="Publisher",
        description="Where the resource is permanently published, indicated the repository, service provider,"
        " or organization that published the resource - e.g., CUAHSI HydroShare."
        " This may be the same as Provider.",
    )
    datePublished: Optional[datetime] = Field(
        title="Date published", description="Date of first publication for the resource."
    )
    subjectOf: Optional[List[SubjectOf]] = Field(
        title="Subject of",
        description="Link to or citation for a related resource that is about or describes this resource"
        " - e.g., a journal paper that describes this resource or a related metadata document "
        "describing the resource.",
    )
    version: Optional[str] = Field(
        description="A text string indicating the version of the resource."
    )  # TODO find something better than float for number
    inLanguage: Optional[Union[LanguageEnum, InLanguageStr]] = Field(
        title="Language", description="The language of the content of the resource."
    )
    creativeWorkStatus: Optional[Union[Draft, Incomplete, Obsolete, Published]] = Field(
        title="Resource status",
        description="The status of this resource in terms of its stage in a lifecycle. "
        "Example terms include Incomplete, Draft, Published, and Obsolete.",
    )
    dateModified: Optional[datetime] = Field(
        title="Date modified", description="The date on which the resource was most recently modified or updated."
    )
    funding: Optional[List[Grant]] = Field(
        description="A Grant or monetary assistance that directly or indirectly provided funding or sponsorship "
        "for creation of the resource.",
    )
    temporalCoverage: Optional[TemporalCoverage] = Field(
        title="Temporal coverage",
        description="The time period that applies to all of the content within the resource.",
    )
    spatialCoverage: Optional[Place] = Field(
        description="The spatialCoverage of a CreativeWork indicates the place(s) which are the focus of the content. "
        "It is a sub property of contentLocation intended primarily for more technical and "
        "detailed materials. For example with a Dataset, it indicates areas that the dataset "
        "describes: a dataset of New York weather would have spatialCoverage which was the "
        "place: the state of New York.",
    )
    hasPart: Optional[List[HasPart]] = Field(
        title="Has part", description="Link to or citation for a related resource that is part of this resource."
    )
    isPartOf: Optional[List[IsPartOf]] = Field(
        title="Is part of",
        description="Link to or citation for a related resource that this resource is a "
        "part of - e.g., a related collection.",
    )
    associatedMedia: Optional[List[MediaObject]] = Field(
        title="Resource content",
        description="A media object that encodes this CreativeWork. This property is a synonym for encoding.",
    )
    citation: Optional[List[str]] = Field(title="Citation", description="A bibliographic citation for the resource.")


class DatasetSchema(CoreMetadata):
    # used only for generating the JSON-LD schema for a dataset.
    pass


class CoreMetadataDOC(CoreMetadata):
    class Settings:
        # name is the collection name in database (iguide) where the Metadata Record documents will be stored
        # for all metadata record types (e.g. dataset, geopackage, software etc.)
        name = "catalog"
        is_root = True
        bson_encoders = {
            date: lambda dt: datetime(year=dt.year, month=dt.month, day=dt.day, hour=0, minute=0, second=0),
            datetime: lambda dt: datetime(
                year=dt.year, month=dt.month, day=dt.day, hour=dt.hour, minute=dt.minute, second=dt.second
            ),
        }
