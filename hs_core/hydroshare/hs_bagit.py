import logging
import mimetypes
import os
import shutil
import tempfile
import zipfile

import bagit
from django.conf import settings
from foresite import utils, Aggregation, AggregatedResource, RdfLibSerializer
from rdflib import Namespace, URIRef

from hs_core.models import ResourceFile


class HsBagitException(Exception):
    pass


def delete_files_and_bag(resource):
    """
    delete the resource bag and all resource files.

    Parameters:
    :param resource: the resource to delete the bag and files for.
    :return: none
    """
    istorage = resource.get_s3_storage()

    # delete resource directory first to remove all generated bag-related files for the resource
    try:
        if istorage.exists(resource.root_path):
            istorage.delete(resource.root_path)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error("cannot remove {}: {}".format(resource.root_path, e))

    delete_bag(resource, istorage)


def delete_bag(resource, istorage=None, raise_on_exception=False):
    """
    delete the resource bag.

    Parameters:
    :param resource: the resource to delete the bag for.
    :param istorage: An S3Storage instance
    :return: none
    """
    if istorage is None:
        istorage = resource.get_s3_storage()

    try:
        if istorage.exists(resource.bag_path):
            istorage.delete(resource.bag_path)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error("cannot remove {}: {}".format(resource.bag_path, e))
        if raise_on_exception:
            raise HsBagitException("failed to remove {}: {}".format(resource.bag_path, e))


def create_bagit_files_by_s3(res, istorage):
    """
    Creates bagit files
    :param res: the resource to create the bag files for
    :param istorage: An S3Storage instance
    :return: None
    """
    resource_id = res.short_id

    from_file_name = getattr(settings, 'HS_BAGIT_README_FILE_WITH_PATH',
                             'docs/bagit/readme.txt')
    istorage.saveFile(from_file_name, f"{resource_id}/readme.txt")
    with tempfile.NamedTemporaryFile() as f:
        f.write(b"BagIt-Version: 0.96\nTag-File-Character-Encoding: UTF-8")
        f.flush()
        istorage.saveFile(f.name, f"{resource_id}/bagit.txt")

    with tempfile.NamedTemporaryFile() as f:
        f.write(b"ace0ef9419c8edbe164a888d4e4ab7ee    bagit.txt\n"
                b"f088113b77567f879055ca48b619928d    manifest-md5.txt\n"
                b"0cc4668a651478cdeb1acc38f73a3b31    readme.txt")
        f.flush()
        istorage.saveFile(f.name, f"{resource_id}/tagmanifest-md5.txt")

    istorage.save_md5_manifest(resource_id)


def save_resource_metadata_xml(resource):
    """
    Writes the resource level metadata from the db to the resourcemetadata.xml file of a resource

    Parameters:
    :param resource: A resource instance
    """
    from hs_core.hydroshare.utils import create_temp_dir_on_s3

    istorage = resource.get_s3_storage()
    temp_path = create_temp_dir_on_s3(istorage)
    from_file_name = os.path.join(temp_path, 'resourcemetadata.xml')
    with open(from_file_name, 'w') as out:
        # write resource level metadata
        out.write(resource.get_metadata_xml())
    to_file_name = os.path.join(resource.root_path, 'data', 'resourcemetadata.xml')
    istorage.saveFile(from_file_name, to_file_name)


def create_bag_metadata_files(resource):
    """
    create and update files needed by bagit operation that is conducted on S3 server;
    no bagit operation is performed, only files that will be included in the bag are created
    or updated.

    Parameters:
    :param resource: A resource whose files will be created or updated to be included in the
    resource bag.
    :return: istorage, an S3Storage object that will be used by subsequent operation to
    create a bag on demand as needed.
    """
    from hs_core.hydroshare.utils import current_site_url, get_file_mime_type, create_temp_dir_on_s3
    from hs_core.hydroshare import encode_resource_url

    istorage = resource.get_s3_storage()

    # the temp_path is a temporary holding path to make the files available to S3
    # we have to make temp_path unique even for the same resource with same update time
    # to accommodate asynchronous multiple file move operations for the same resource

    # TODO: This is always in /tmp; otherwise code breaks because open() is called on the result!
    temp_path = create_temp_dir_on_s3(istorage)

    # an empty visualization directory will not be put into the zipped bag file by ibun command,
    # so creating an empty visualization directory to be put into the zip file as done by the two
    # statements below does not work. However, if visualization directory has content to be
    # uploaded, it will work. This is to be implemented as part of the resource model in the future.
    # The following two statements are placeholders serving as reminder
    # to_file_name = '{res_id}/data/visualization/'.format(res_id=resource.short_id)
    # istorage.saveFile('', to_file_name, create_directory=True)

    # create resourcemetadata.xml in local directory and upload it to S3
    save_resource_metadata_xml(resource)

    # URLs are found in the /data/ subdirectory to comply with bagit format assumptions
    current_site_url = current_site_url()
    # This is the qualified resource url.
    hs_res_url = os.path.join(current_site_url, 'resource', resource.short_id, 'data')
    # this is the path to the resourcemedata file for download
    metadata_url = os.path.join(hs_res_url, 'resourcemetadata.xml')
    # this is the path to the resourcemap file for download
    res_map_url = os.path.join(hs_res_url, 'resourcemap.xml')

    # make the resource map:
    utils.namespaces['citoterms'] = Namespace('http://purl.org/spar/cito/')
    utils.namespaceSearchOrder.append('citoterms')

    ag_url = os.path.join(hs_res_url, 'resourcemap.xml#aggregation')
    a = Aggregation(ag_url)

    # Set properties of the aggregation
    a._dc.title = resource.metadata.title.value
    a._dcterms.type = URIRef(resource.metadata.type.url)
    a._citoterms.isDocumentedBy = metadata_url
    a._ore.isDescribedBy = res_map_url

    res_type_aggregation = AggregatedResource(resource.metadata.type.url)
    res_type_aggregation._rdfs.label = resource._meta.verbose_name
    res_type_aggregation._rdfs.isDefinedBy = current_site_url + "/terms"

    a.add_resource(res_type_aggregation)

    # Create a description of the metadata document that describes the whole resource and add it
    # to the aggregation
    resMetaFile = AggregatedResource(metadata_url)
    resMetaFile._dc.title = "Dublin Core science metadata document describing the HydroShare " \
                            "resource"
    resMetaFile._citoterms.documents = ag_url
    resMetaFile._ore.isAggregatedBy = ag_url
    resMetaFile._dc.format = "application/rdf+xml"
    a.add_resource(resMetaFile)

    # Add the resource files to the aggregation
    files = ResourceFile.objects.filter(object_id=resource.id)

    for f in files:
        # only the files that are not part of file type aggregation (logical file)
        # should be added to the resource level map xml file
        if f.logical_file is None:
            short_path = f.get_short_path(resource=resource)
            res_uri = '{hs_url}/resource/{res_id}/data/contents/{file_name}'.format(
                hs_url=current_site_url,
                res_id=resource.short_id,
                file_name=short_path)
            res_uri = encode_resource_url(res_uri)
            ar = AggregatedResource(res_uri)
            ar._ore.isAggregatedBy = ag_url
            ar._dc.format = get_file_mime_type(os.path.basename(short_path))
            a.add_resource(ar)

    # handle collection resource type
    # save contained resource urls into resourcemap.xml
    if resource.resource_type == "CollectionResource" and resource.resources:
        for contained_res in resource.resources.all():
            contained_res_id = contained_res.short_id
            resource_map_url = '{hs_url}/resource/{res_id}/data/resourcemap.xml'.format(
                hs_url=current_site_url,
                res_id=contained_res_id)

            ar = AggregatedResource(resource_map_url)
            ar._ore.isAggregatedBy = ag_url
            ar._dc.format = "application/rdf+xml"
            a.add_resource(ar)
    elif resource.resource_type == "CompositeResource":
        # add file type aggregations to resource aggregation
        for logical_file in resource.logical_files:
            if logical_file.has_parent:
                # skip nested aggregations
                continue
            aggr_uri = '{hs_url}/resource/{res_id}/data/contents/{map_file_path}#aggregation'
            aggr_uri = aggr_uri.format(
                hs_url=current_site_url,
                res_id=resource.short_id,
                map_file_path=logical_file.map_short_file_path)
            aggr_uri = encode_resource_url(aggr_uri)
            agg = Aggregation(aggr_uri)
            agg._ore.isAggregatedBy = ag_url
            agg_type_url = "{site}/terms/{aggr_type}"
            agg_type_url = agg_type_url.format(site=current_site_url,
                                               aggr_type=logical_file.get_aggregation_type_name())
            agg._dcterms.type = URIRef(agg_type_url)
            a.add_resource(agg)

    # Register a serializer with the aggregation, which creates a new ResourceMap that needs a URI
    serializer = RdfLibSerializer('xml')
    resMap = a.register_serialization(serializer, res_map_url)
    resMap._dc.identifier = resource.short_id

    # Fetch the serialization
    remdoc = a.get_serialization()

    # change the namespace for the 'creator' element from 'dcterms' to 'dc'
    xml_string = remdoc.data.replace('dcterms:creator', 'dc:creator')

    # delete this extra element
    # <ore:aggregates rdf:resource="[hydroshare domain]/terms/[Resource class name]"/>
    xml_string = xml_string.replace(
        '<ore:aggregates rdf:resource="%s"/>\n' % str(resource.metadata.type.url), '')

    # create resourcemap.xml and upload it to S3
    from_file_name = os.path.join(temp_path, 'resourcemap.xml')
    with open(from_file_name, 'w') as out:
        out.write(xml_string)
    to_file_name = os.path.join(resource.root_path, 'data', 'resourcemap.xml')
    istorage.saveFile(from_file_name, to_file_name)

    # if the resource is a composite resource generate aggregation meta files (res map, metadata xml and schema json)
    # files
    if resource.resource_type == "CompositeResource":
        resource.create_aggregation_meta_files()

    res_coll = resource.root_path
    istorage.setAVU(res_coll, 'metadata_dirty', "false")
    shutil.rmtree(temp_path)
    return istorage


def create_bag(resource):
    """
    Creates bagit files on S3

    Parameters:
    :param resource: (subclass of AbstractResource) A resource to create a bag for.
    :return: the hs_core.models.Bags instance associated with the new bag.
    """
    create_bag_metadata_files(resource)

    # set bag_modified-true AVU pair for on-demand bagging.to indicate the resource bag needs to be
    # created when user clicks on download button
    resource.setAVU("bag_modified", True)

    return


def read_bag(bag_path):
    """
    :param bag_path:
    :return:
    """

    tmpdir = None

    try:
        if not os.path.exists(bag_path):
            raise HsBagitException('Bag does not exist')
        if os.path.isdir(bag_path):
            unpacked_bag_path = bag_path
        else:
            mtype = mimetypes.guess_type(bag_path)
            if mtype[0] != 'application/zip':
                msg = "Expected bag to have MIME type application/zip, " \
                      "but it has {0} instead.".format(mtype[0])
                raise HsBagitException(msg)
            tmpdir = tempfile.mkdtemp()
            zfile = zipfile.ZipFile(bag_path)
            zroot = zfile.namelist()[0].split(os.sep)[0]
            zfile.extractall(tmpdir)
            unpacked_bag_path = os.path.join(tmpdir, zroot)

        bag = bagit.Bag(unpacked_bag_path)
        if not bag.is_valid():
            msg = "Bag is not valid"
            raise HsBagitException(msg)

    finally:
        if tmpdir:
            shutil.rmtree(tmpdir)
