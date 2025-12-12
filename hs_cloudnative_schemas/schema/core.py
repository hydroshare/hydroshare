from datetime import datetime
from typing import List, Optional, Union


from pydantic import (
    Field,
    HttpUrl,
)

from .base import (
    CreativeWork,
    SchemaBaseModel,
    Creator,
    Contributor,
    Organization,
    Provider,
    PublisherOrganization,
    SubjectOf,
    LanguageEnum,
    InLanguageStr,
    Draft,
    Incomplete,
    Obsolete,
    Published,
    Public,
    Discoverable,
    Grant,
    TemporalCoverage,
    Place,
    HasPart,
    IsPartOf,
    MediaType,
    PropertyValue,
)


class CoreMetadata(SchemaBaseModel):

    ###################
    # REQUIRED FIELDS #
    ###################
    context: HttpUrl = Field(
        alias="@context",  # type: ignore
        default=HttpUrl(
            "https://hydroshare.org/schema"
        ),  # TODO: This is a placeholder for now.
        description="Specifies the vocabulary employed for understanding the structured data markup.",
    )
    type: str = Field(
        alias="@type",  # type: ignore
        default="CreativeWork",
        description="A creative work that may include various forms of content, such as datasets,"
        " software source code, digital documents, etc.",
        #        json_schema_extra={
        #            "enum": ["Dataset", "Notebook", "Software Source Code"],
        #        },
    )
    additionalType: Optional[str] = Field(
        title="Additional type",
        description="An additional type for the resource. This can be used to further specify the type of the"
                    " resource (e.g., Composite Resource).",
    )
    name: str = Field(
        title="Name or title",
        description="A text string with a descriptive name or title for the resource.",
    )
    description: str = Field(
        title="Description or abstract",
        description="A text string containing a description/abstract for the resource.",
    )
    url: HttpUrl = Field(
        title="URL",
        description="A URL for the landing page that describes the resource and where the content "
        "of the resource can be accessed. If there is no landing page,"
        " provide the URL of the content.",
    )
    identifier: List[str] = Field(
        title="Identifiers",
        description="Any kind of identifier for the resource. Identifiers may be DOIs or unique strings "
        "assigned by a repository. Multiple identifiers can be entered. Where identifiers can be "
        "encoded as URLs, enter URLs here.",
    )

    creator: List[Union[Creator, Organization]] = Field(
        description="Person or Organization that created the resource."
    )
    dateCreated: datetime = Field(
        title="Date created", description="The date on which the resource was created."
    )
    keywords: List[str] = Field(
        min_length=1,
        description="Keywords or tags used to describe the dataset, delimited by commas.",
    )
    license: Union[CreativeWork, HttpUrl] = Field(
        description="A license document that applies to the resource."
    )
    provider: Union[Organization, Provider] = Field(
        description="The repository, service provider, organization, person, or service performer that provides"
        " access to the resource."
    )

    ###################
    # OPTIONAL FIELDS #
    ###################
    contributor: Optional[List[Union[Contributor, Organization]]] = Field(
        description="Person or Organization that contributed to the resource.",
        default=None
    )
    publisher: Optional[PublisherOrganization] = Field(
        title="Publisher",
        description="Where the resource is permanently published, indicated the repository, service provider,"
        " or organization that published the resource - e.g., CUAHSI HydroShare."
        " This may be the same as Provider.",
        default=None,
    )
    datePublished: Optional[datetime] = Field(
        title="Date published",
        description="Date of first publication for the resource.",
        default=None,
    )
    subjectOf: Optional[List[SubjectOf]] = Field(
        title="Subject of",
        description="Link to or citation for a related resource that is about or describes this resource"
        " - e.g., a journal paper that describes this resource or a related metadata document "
        "describing the resource.",
        default=None,
    )
    version: Optional[str] = Field(
        description="A text string indicating the version of the resource.",
        default=None,
    )  # TODO find something better than float for number
    inLanguage: Optional[Union[LanguageEnum, InLanguageStr]] = Field(
        title="Language",
        description="The language of the content of the resource.",
        default=None,
    )
    creativeWorkStatus: Optional[Union[Draft, Incomplete, Obsolete, Published, Public, Discoverable]] = Field(
        title="Resource status",
        description="The status of this resource in terms of its stage in a lifecycle. "
        "Example terms include Incomplete, Draft, Published, and Obsolete.",
        default=None,
    )
    dateModified: Optional[datetime] = Field(
        title="Date modified",
        description="The date on which the resource was most recently modified or updated.",
        default=None,
    )
    funding: Optional[List[Grant]] = Field(
        description="A Grant or monetary assistance that directly or indirectly provided funding or sponsorship "
        "for creation of the resource.",
        default=None,
    )
    temporalCoverage: Optional[TemporalCoverage] = Field(
        title="Temporal coverage",
        description="The time period that applies to all of the content within the resource.",
        default=None,
    )
    spatialCoverage: Optional[Place] = Field(
        description="The spatialCoverage of a CreativeWork indicates the place(s) which are the focus of the content. "
        "It is a sub property of contentLocation intended primarily for more technical and "
        "detailed materials. For example with a Dataset, it indicates areas that the dataset "
        "describes: a dataset of New York weather would have spatialCoverage which was the "
        "place: the state of New York.",
        default=None,
    )
    hasPart: Optional[List[HasPart]] = Field(
        title="Has part",
        description="Link to or citation for a related resource that is part of this resource.",
        default=None,
    )
    isPartOf: Optional[List[IsPartOf]] = Field(
        title="Is part of",
        description="Link to or citation for a related resource that this resource is a "
        "part of - e.g., a related collection.",
        default=None,
    )
    additionalProperty: Optional[List[PropertyValue]] = Field(
        title="Additional properties",
        default=None,
        description="Additional properties of the place.",
    )

    # using MediaType here to allow for MediaObject and its subclasses (e.g., DataDownload, VideoObject)
    associatedMedia: Optional[Union[MediaType, List[MediaType]]] = Field(
        title="Resource content",
        description="A media object that encodes this CreativeWork. This property is a synonym for encoding.",
        default=None,
    )
    citation: Optional[List[str]] = Field(
        title="Citation",
        description="A bibliographic citation for the resource.",
        default=None,
    )
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            HttpUrl: str,  # Convert HttpUrl to a string during serialization
        },
    }
