from .core import CoreMetadata
from enum import Enum
from typing import ClassVar, Optional, List, Union, Literal
from pydantic import Field, HttpUrl, model_serializer
from datetime import datetime

from .base import (
    PropertyValue,
    Organization,
    DataCatalog,
    Creator,
    CreativeWork,
    Provider,
    LinkedData,
    MediaType,
)

from .datavariable import Dimension, DataVariable


class AdditionalType(str, Enum):
    GEOGRAPHIC_FEATURE = 'GeographicFeature'
    GEOGRAPHIC_RASTER = 'GeographicRaster'
    MULTIDIMENSIONAL = 'MultiDimensional'
    TABULAR = 'Tabular'


class ScientificDataset(CoreMetadata):
    """
    A generic dataset extends the CoreMetadata class with a few additional fields and is designed to capture
    scientific file-level metadata.. It also overrides many of the required CoreMetadata fields to make them
    optional. It generally follows the design of the Schema.org Dataset class.
    """

    context: HttpUrl = Field(
        alias="@context",  # type: ignore
        default=HttpUrl(
            "https://hydroshare.org/schema"
        ),  # TODO: This is a placeholder for now.
        description="Specifies the vocabulary employed for understanding the structured data markup.",
    )
    type: Literal["ScientificDataset"] = Field(
        alias="@type",  # type: ignore
        default="ScientificDataset",
        description="A body of structured information describing some topic(s) of interest.",
    )

    variableMeasured: List[Union[str, PropertyValue, DataVariable]] = Field(
        title="Variables measured", description="Measured variables."
    )

    dimensions: List[Dimension] = Field(
        title="Dimensions",
        description="Dimensions defined in the multi-dimensional dataset.",
    )

    # redefine associatedMedia from "Core" to also accept a single (non-list) value
    associatedMedia: Union[LinkedData, MediaType, List[Union[LinkedData, MediaType]]] = Field(
        title="Resource content",
        description="A media object that encodes this CreativeWork. This property is a synonym for encoding.",
        default=[]
    )

    coordinates: Optional[List[DataVariable]] = Field(
        default=None,
        title="Coordinates",
        description="Coordinate variables that provide values along a dimension",
    )

    includedInDataCatalog: Optional[DataCatalog] = Field(
        default=None,
        title="DataCatalog",
        description="A data catalog which contains this dataset.",
    )

    additionalProperty: Optional[
        Union[str, List[str], PropertyValue, List[PropertyValue]]
    ] = Field(
        title="Additional properties",
        default=None,
        description="Additional properties of the dataset that don't fit into schema org.",
    )
    sourceOrganization: Optional[Organization] = Field(
        default=None,
        title="Source organization",
        description="The organization that provided the data for this dataset.",
    )
    additionalType: Optional[AdditionalType] = Field(
        default=None,
        title="Additional Type",
        description="Additional descriptive types associated with the ScientificDataset. This is typically used by "
        "applications to provide specialized funcationality for categories for content."
    )

    # ---------------------------------------------
    # make required CoreMetadata fields "Optional",
    # but preserve the metadata defined in the
    # parent class
    # ---------------------------------------------
    name: Optional[str] = Field(
        default=None,
        title="Name or title",
        description="A text string with a descriptive name or title for the resource.",
    )
    description: Optional[str] = Field(
        default=None,
        title="Description or abstract",
        description="A text string containing a description/abstract for the resource.",
    )
    url: Optional[HttpUrl] = Field(
        default=None,
        title="URL",
        description="A URL for the landing page that describes the resource and where the content "
        "of the resource can be accessed. If there is no landing page,"
        " provide the URL of the content.",
    )
    identifier: Optional[List[str]] = Field(
        default=None,
        title="Identifiers",
        description="Any kind of identifier for the resource. Identifiers may be DOIs or unique strings "
        "assigned by a repository. Multiple identifiers can be entered. Where identifiers can be "
        "encoded as URLs, enter URLs here.",
    )

    creator: Optional[List[Union[Creator, Organization]]] = Field(
        default=None, description="Person or Organization that created the resource."
    )
    dateCreated: Optional[datetime] = Field(
        default=None,
        title="Date created",
        description="The date on which the resource was created.",
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Keywords or tags used to describe the dataset, delimited by commas.",
    )
    license: Optional[Union[CreativeWork, HttpUrl]] = Field(
        default=None, description="A license document that applies to the resource."
    )
    provider: Optional[Union[Organization, Provider]] = Field(
        default=None,
        description="The repository, service provider, organization, person, or service performer that provides"
        " access to the resource.",
    )

    # Fields that are dropped from serialized output when they hold no value (None or []).
    _OMIT_WHEN_EMPTY: ClassVar[tuple] = ("coordinates", "sourceOrganization", "associatedMedia")

    @model_serializer(mode="wrap")
    def _omit_when_empty(self, handler):
        """Drop fields listed in _OMIT_WHEN_EMPTY from the serialized output when they are empty.

        These fields are populated only for some content types (e.g., NetCDF coordinates) and
        are otherwise always null/empty in the generated schema.org metadata. The defaults are kept
        (rather than removed) so that validated construction, e.g. ScientificDataset(...) in the
        hs_extract raster/feature extractors, does not fail with 'Field required'.
        """
        data = handler(self)
        if isinstance(data, dict):
            for field_name in self._OMIT_WHEN_EMPTY:
                if field_name in data and data[field_name] in (None, []):
                    del data[field_name]
        return data
