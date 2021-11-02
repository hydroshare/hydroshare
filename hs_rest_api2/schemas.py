from typing import Dict, List, Union

from hsmodels.schemas.fields import AwardInfo, PointCoverage, BoxCoverage, PeriodCoverage, Publisher, Creator, Contributor, Relation, Rights
from hsmodels.schemas.root_validators import split_coverages, parse_additional_metadata
from pydantic import Field, root_validator, validator

from hsmodels.schemas.base_models import BaseMetadata

from hsmodels.schemas.validators import (
    parse_spatial_coverage,
)


def parse_abstract(cls, values):
    if "description" in values:
        value = values["description"]
        if isinstance(value, dict) and "abstract" in value:
            values['abstract'] = value['abstract']
            del values['description']
    return values


def parse_sources(cls, value):
    if len(value) > 0 and isinstance(value[0], dict):
        return [f['is_derived_from'] for f in value]
    return value


class ResourceMetadataIn(BaseMetadata):
    """
    A class used to represent the metadata for a resource that can be modified
    """

    class Config:
        title = 'Resource Metadata'

    title: str = Field(
        max_length=300, default=None, title="Title", description="A string containing the name given to a resource"
    )
    abstract: str = Field(default=None, title="Abstract", description="A string containing a summary of a resource")
    language: str = Field(
        title="Language",
        description="A 3-character string for the language in which the metadata and content of a resource are expressed",
        default='eng'
    )
    subjects: List[str] = Field(
        default=[], title="Subject keywords", description="A list of keyword strings expressing the topic of a resource"
    )
    creators: List[Creator] = Field(
        default=[],
        title="Creators",
        description="A list of Creator objects indicating the entities responsible for creating a resource",
    )
    contributors: List[Contributor] = Field(
        default=[],
        title="Contributors",
        description="A list of Contributor objects indicating the entities that contributed to a resource",
    )
    sources: List[str] = Field(
        default=[],
        title="Sources",
        description="A list of strings containing references to related resources from which a described resource was derived",
    )
    relations: List[Relation] = Field(
        default=[],
        title="Related resources",
        description="A list of Relation objects representing resources related to a described resource",
    )
    additional_metadata: Dict[str, str] = Field(
        default={},
        title="Additional metadata",
        description="A dictionary containing key-value pair metadata associated with a resource",
    )
    rights: Rights = Field(
        title="Rights", description="An object containing information about rights held in an over a resource",
        default_factory=Rights.Creative_Commons_Attribution_CC_BY
    )
    awards: List[AwardInfo] = Field(
        default=[],
        title="Funding agency information",
        description="A list of objects containing information about the funding agencies and awards associated with a resource",
    )
    spatial_coverage: Union[PointCoverage, BoxCoverage] = Field(
        default=None,
        title="Spatial coverage",
        description="An object containing information about the spatial topic of a resource, the spatial applicability of a resource, or jurisdiction under with a resource is relevant",
    )
    period_coverage: PeriodCoverage = Field(
        default=None,
        title="Temporal coverage",
        description="An object containing information about the temporal topic or applicability of a resource",
    )
    publisher: Publisher = Field(
        default=None,
        title="Publisher",
        description="An object containing information about the publisher of a resource",
    )
    citation: str = Field(
        default=None, title="Citation", description="A string containing the biblilographic citation for a resource"
    )

    _parse_coverages = root_validator(pre=True, allow_reuse=True)(split_coverages)
    _parse_additional_metadata = root_validator(pre=True, allow_reuse=True)(parse_additional_metadata)
    _parse_abstract = root_validator(pre=True)(parse_abstract)
    _parse_sources = validator("sources", pre=True)(parse_sources)
    _parse_spatial_coverage = validator("spatial_coverage", allow_reuse=True, pre=True)(parse_spatial_coverage)
