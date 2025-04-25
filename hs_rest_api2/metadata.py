import json
import logging
from datetime import datetime, timezone

from django.db import transaction
from hsmodels.schemas import ResourceMetadata, load_rdf, rdf_graph
from pydantic import ConfigDict
from pydantic import ValidationError as PydanticValidationError
from rest_framework.exceptions import ValidationError

from hs_core.hydroshare.hs_bagit import save_resource_metadata_xml
from hs_file_types.utils import ingest_logical_file_metadata
from hs_rest_api2.serializers import ResourceMetadataInForbidExtra

logger = logging.getLogger(__name__)


def _get_in_schema(out_schema):
    """
    Gets the parent schema class and subclasses it to forbid extra parameters

    :params out_schema: A hsmodel schema

    :returns: A new schema class
    """
    in_schema = out_schema.__bases__[0]

    class IncomingForbid(in_schema):
        model_config = ConfigDict(extra="forbid")

    return IncomingForbid


def load_metadata_from_file(istorage, file_with_path):
    """
    Loads a rdf/xml metadata file to a hsmodel pydantic schema instance

    Parameters:
    :param istorage: An S3 storage object
    :param file_with_path: The path to the rdf/xml metadata file

    :returns: hsmodel schema instance
    """
    with istorage.open(file_with_path) as f:
        metadata = load_rdf(f.read())
        return metadata


def resource_metadata(resource):
    """
    Loads the resource rdf/xml file to a hsmodel pydantic schema instance

    Parameters:
    :param resource: A resource django model instance

    :returns: ResourceMetadata schema instance
    """
    file_with_path = resource.scimeta_path
    istorage = resource.get_s3_storage()
    resource.update_relation_meta()
    metadata_dirty = resource.getAVU("metadata_dirty")
    if metadata_dirty:
        save_resource_metadata_xml(resource)
    return load_metadata_from_file(istorage, file_with_path)


def resource_metadata_json_loads(resource):
    """
    Returns the resource metadata as a JSON dict
    """
    return json.loads(resource_metadata(resource).model_dump_json())


def ingest_resource_metadata(resource, incoming_metadata):
    """
    Writes resource metadata json to the resource rdf/xml.

    Parameters:
    :param resource: A resource django model instance
    :param incoming_metadata: JSON dictionary of resource metadata

    :returns: ResourceMetadata schema instance

    :raises: ValidationError when incoming_metadata does not pass validation
    """
    r_md = resource_metadata(resource).model_dump()
    try:
        incoming_r_md = ResourceMetadataInForbidExtra(**incoming_metadata)
    except PydanticValidationError as e:
        raise ValidationError(e)
    # merge existing metadata with incoming, incoming overrides existing
    merged_metadata = {
        **r_md,
        **incoming_r_md.model_dump(exclude_defaults=True),
        "modified": datetime.now(timezone.utc).isoformat(),
    }
    res_metadata = ResourceMetadata(**merged_metadata)

    graph = rdf_graph(res_metadata)
    try:
        with transaction.atomic():
            resource.metadata.delete_all_elements()
            resource.metadata.ingest_metadata(graph)
    except: # noqa
        logger.exception(
            f"Error processing resource metadata file for resource {resource.short_id}"
        )
        raise
    save_resource_metadata_xml(resource)
    return json.loads(res_metadata.model_dump_json())


def ingest_aggregation_metadata(resource, incoming_metadata, file_path):
    """
    Writes resource metadata json to the resource rdf/xml.

    Parameters:
    :param resource: A resource django model instance
    :param incoming_metadata: JSON dictionary of resource metadata

    :returns: ResourceMetadata schema instance

    :raises: ValidationError when incoming_metadata does not pass validation
    """
    aggregation = resource.get_aggregation_by_name(file_path)
    if aggregation.metadata.is_dirty:
        aggregation.create_aggregation_xml_documents()

    # read existing metadata from file
    agg_md = load_metadata_from_file(
        resource.get_s3_storage(), aggregation.metadata_file_path
    )

    agg_md_dict = agg_md.model_dump()

    # get schema classes
    out_schema = agg_md.__class__
    in_schema = _get_in_schema(out_schema)

    # validate incoming metadata against the schema
    try:
        incoming_md = in_schema(**incoming_metadata)
    except PydanticValidationError as e:
        raise ValidationError(e)

    # merge existing metadata with incoming, incoming overrides existing
    incoming_dict = {**incoming_md.model_dump(exclude_defaults=True)}
    existing_dict = {**agg_md_dict}
    merged_metadata = {**existing_dict, **incoming_dict}

    agg_metadata = out_schema(**merged_metadata)
    graph = rdf_graph(agg_metadata)

    # write the updated metadata back to file
    ingest_logical_file_metadata(graph, resource)
    aggregation.refresh_from_db()
    return json.loads(agg_metadata.model_dump_json())


def aggregation_metadata_json_loads(resource, file_path):
    """
    Returns the aggregation metadata as a JSON dict
    """
    agg = resource.get_aggregation_by_name(file_path)
    if agg.metadata.is_dirty:
        agg.create_aggregation_xml_documents()
    agg_md = load_metadata_from_file(
        resource.get_s3_storage(), agg.metadata_file_path
    )
    return json.loads(agg_md.model_dump_json())
