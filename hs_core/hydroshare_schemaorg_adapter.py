from datetime import datetime
from typing import Any, List, Optional, Union, Literal

from pydantic import BaseModel, HttpUrl, ConfigDict, model_validator

from hs_cloudnative_schemas.schema import base as schema
from hs_cloudnative_schemas.schema.dataset import ScientificDataset


class BasePerson(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    organization: Optional[str] = None
    homepage: Optional[HttpUrl] = None
    address: Optional[str] = None
    identifiers: Optional[dict] = {}

    def to_dataset_person(self, person_type):
        if self.name:
            person = person_type.construct()
            person.name = self.name
            if self.email:
                person.email = self.email
            if self.organization:
                affiliation = schema.Organization.construct()
                affiliation.name = self.organization
                person.affiliation = affiliation
            _ORCID_identifier = self.identifiers.get("ORCID", "")
            if _ORCID_identifier:
                person.identifier = _ORCID_identifier
        else:
            person = schema.Organization.construct()
            person.name = self.organization
            if self.homepage:
                person.url = self.homepage
            if self.address:
                person.address = self.address

        return person


class Creator(BasePerson):

    def to_dataset_creator(self):
        return self.to_dataset_person(schema.Creator)


class Contributor(BasePerson):

    def to_dataset_contributor(self):
        return self.to_dataset_person(schema.Contributor)


class Award(BaseModel):
    funding_agency_name: str
    title: Optional[str] = None
    number: Optional[str] = None
    funding_agency_url: Optional[HttpUrl] = None

    def to_dataset_grant(self):
        grant = schema.Grant.construct()
        if self.title:
            grant.name = self.title
        else:
            grant.name = self.funding_agency_name
        if self.number:
            grant.identifier = self.number

        funder = schema.Organization.construct()
        funder.name = self.funding_agency_name
        if self.funding_agency_url:
            funder.url = self.funding_agency_url

        grant.funder = funder
        return grant


class TemporalCoverage(BaseModel):
    start: datetime
    end: datetime

    def to_dataset_temporal_coverage(self):
        temp_cov = schema.TemporalCoverage.construct()
        if self.start:
            temp_cov.startDate = self.start
            if self.end:
                temp_cov.endDate = self.end
        return temp_cov


class SpatialCoverageBox(BaseModel):
    name: Optional[str] = None
    northlimit: float
    eastlimit: float
    southlimit: float
    westlimit: float

    def to_dataset_spatial_coverage(self):
        place = schema.Place.construct()
        if self.name:
            place.name = self.name

        place.geo = schema.GeoShape.construct()
        place.geo.box = f"{self.northlimit} {self.eastlimit} {self.southlimit} {self.westlimit}"
        return place


class SpatialCoveragePoint(BaseModel):
    name: Optional[str] = None
    north: float
    east: float

    def to_dataset_spatial_coverage(self):
        place = schema.Place.construct()
        if self.name:
            place.name = self.name
        place.geo = schema.GeoCoordinates.construct()
        place.geo.latitude = self.north
        place.geo.longitude = self.east
        return place


class ContentFile(BaseModel):
    path: str
    size: int
    mime_type: str = None
    checksum: str

    def to_dataset_media_object(self):
        media_object = schema.MediaObject.construct()
        media_object.contentUrl = self.path
        media_object.encodingFormat = self.mime_type
        media_object.contentSize = f"{self.size / 1000.00} KB"
        if "/" in self.path:
            media_object.name = self.path.split("/")[-1]
        else:
            media_object.name = self.path
        return media_object


class Relation(BaseModel):
    type: str
    value: str

    def to_dataset_part_relation(self, relation_type: str):
        relation = None
        if relation_type == "IsPartOf" and self.type.endswith("is part of"):
            relation = schema.IsPartOf.construct()
        elif relation_type == "HasPart" and self.type.endswith("resource includes"):
            relation = schema.HasPart.construct()
        else:
            relation = schema.Relation.construct()
            relation.name = self.type

        if ',' in self.value:
            description, url = self.value.rsplit(',', 1)
        else:
            description, url = self.value, ""
        relation.description = description.strip()
        relation.url = url.strip()
        return relation


class Rights(BaseModel):
    statement: Optional[str] = None
    url: Optional[HttpUrl] = None

    def to_dataset_license(self):
        _license = schema.CreativeWork.construct()
        _license.name = self.statement
        _license.url = self.url
        return _license


class HydroshareMetadataAdapter:
    @staticmethod
    def to_catalog_record(metadata: dict):
        """Converts hydroshare resource metadata to a catalog dataset record"""
        hs_metadata_model = _HydroshareResourceMetadata(**metadata)
        if metadata["type"] == "CompositeResource":
            return hs_metadata_model.to_catalog_dataset()
        return hs_metadata_model.to_catalog_dataset()


class _HydroshareResourceMetadata(BaseModel):
    model_config = ConfigDict(extra='allow')

    type: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[HttpUrl] = None
    identifier: Optional[HttpUrl] = None
    creators: List[Creator] = []
    contributors: List[Contributor] = []
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    published: Optional[datetime] = None
    subjects: Optional[List[str]] = None
    language: Optional[str] = None
    rights: Optional[Rights] = None
    awards: List[Award] = []
    spatial_coverage: Optional[Union[SpatialCoverageBox, SpatialCoveragePoint]] = None
    period_coverage: Optional[TemporalCoverage] = None
    relations: List[Relation] = []
    citation: Optional[str] = None
    associatedMedia: List[Any] = []
    sharing_status: Optional[Literal["private", "public", "published", "discoverable"]] = None

    @model_validator(mode="before")
    @classmethod
    def set_extra_columns(cls, data: Any):
        if isinstance(data, dict):
            extra_fields = data.keys() - cls.model_fields.keys()
            if extra_fields:
                if "extra_columns" not in data:
                    data["extra_columns"] = {}
                data["extra_columns"].update(
                    {field_name: data[field_name] for field_name in extra_fields}
                )
        return data

    def to_dataset_creators(self):
        creators = []
        for creator in self.creators:
            creators.append(creator.to_dataset_creator())
        return creators

    def to_dataset_contributors(self):
        contributors = []
        for contributor in self.contributors:
            contributors.append(contributor.to_dataset_contributor())
        return contributors

    def to_dataset_funding(self):
        grants = []
        for award in self.awards:
            grants.append(award.to_dataset_grant())
        return grants

    def to_dataset_associated_media(self):
        return self.associatedMedia

    def to_dataset_is_part_of(self):
        return self._to_dataset_part_relations("IsPartOf")

    def to_dataset_has_part(self):
        return self._to_dataset_part_relations("HasPart")

    def to_dataset_relations(self):
        return self._to_dataset_part_relations("Other")

    def _to_dataset_part_relations(self, relation_type: str):
        part_relations = []
        for relation in self.relations:
            part_relation = relation.to_dataset_part_relation(relation_type)
            if part_relation:
                part_relations.append(part_relation)
        return part_relations

    def to_dataset_spatial_coverage(self):
        if self.spatial_coverage:
            return self.spatial_coverage.to_dataset_spatial_coverage()
        return None

    def to_dataset_period_coverage(self):
        if self.period_coverage:
            return self.period_coverage.to_dataset_temporal_coverage()
        return None

    def to_dataset_keywords(self):
        if self.subjects:
            return self.subjects
        return ["HydroShare"]

    def to_dataset_license(self):
        if self.rights:
            return self.rights.to_dataset_license()

    def to_dataset_creative_work_status(self):
        status_defined_terms = {
            "public": schema.Public,
            "published": schema.Published,
            "discoverable": schema.Discoverable,
            "private": schema.Private,
        }
        if self.sharing_status:
            return status_defined_terms[self.sharing_status].construct()

    @staticmethod
    def to_dataset_provider():
        provider = schema.Organization.construct()
        provider.name = "HydroShare"
        provider.url = "https://www.hydroshare.org/"
        return provider

    def to_catalog_dataset(self):
        dataset = ScientificDataset.model_construct(**self.extra_columns)
        dataset.additionalType = self.type
        dataset.provider = self.to_dataset_provider()
        dataset.name = self.title
        dataset.description = self.abstract
        dataset.url = self.url
        dataset.identifier = [self.identifier]
        dataset.creator = self.to_dataset_creators()
        dataset.contributor = self.to_dataset_contributors()
        dataset.dateCreated = self.created
        dataset.dateModified = self.modified
        dataset.datePublished = self.published
        dataset.keywords = self.to_dataset_keywords()
        dataset.inLanguage = self.language
        dataset.funding = self.to_dataset_funding()
        dataset.spatialCoverage = self.to_dataset_spatial_coverage()
        dataset.temporalCoverage = self.to_dataset_period_coverage()
        dataset.associatedMedia = self.to_dataset_associated_media()
        dataset.isPartOf = self.to_dataset_is_part_of()
        dataset.hasPart = self.to_dataset_has_part()
        dataset.license = self.to_dataset_license()
        dataset.citation = [self.citation]
        dataset.creativeWorkStatus = self.to_dataset_creative_work_status()
        dataset.relations = self.to_dataset_relations()
        return dataset
