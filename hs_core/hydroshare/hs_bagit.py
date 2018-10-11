import os
import shutil
import errno
import tempfile
import mimetypes
import zipfile

from uuid import uuid4

from foresite import utils, Aggregation, AggregatedResource, RdfLibSerializer
from rdflib import Namespace, URIRef

import bagit
from mezzanine.conf import settings
from hs_core.models import Bags, ResourceFile


class HsBagitException(Exception):
    pass


def delete_files_and_bag(resource):
    """
    delete the resource bag and all resource files.

    Parameters:
    :param resource: the resource to delete the bag and files for.
    :return: none
    """
    istorage = resource.get_irods_storage()

    # delete resource directory first to remove all generated bag-related files for the resource
    if istorage.exists(resource.root_path):
        istorage.delete(resource.root_path)

    if istorage.exists(resource.bag_path):
        istorage.delete(resource.bag_path)

    # TODO: delete this whole mechanism; redundant.
    # delete the bags table
    for bag in resource.bags.all():
        bag.delete()


def create_bag_files(resource):
    """
    create and update files needed by bagit operation that is conducted on iRODS server;
    no bagit operation is performed, only files that will be included in the bag are created
    or updated.

    Parameters:
    :param resource: A resource whose files will be created or updated to be included in the
    resource bag.
    :return: istorage, an IrodsStorage object that will be used by subsequent operation to
    create a bag on demand as needed.
    """
    from hs_core.hydroshare.utils import current_site_url, get_file_mime_type

    istorage = resource.get_irods_storage()

    # the temp_path is a temporary holding path to make the files available to iRODS
    # we have to make temp_path unique even for the same resource with same update time
    # to accommodate asynchronous multiple file move operations for the same resource

    # TODO: This is always in /tmp; otherwise code breaks because open() is called on the result!
    temp_path = os.path.join(getattr(settings, 'IRODS_ROOT', '/tmp'), uuid4().hex)

    try:
        os.makedirs(temp_path)
    except OSError as ex:
        # TODO: there might be concurrent operations.
        if ex.errno == errno.EEXIST:
            shutil.rmtree(temp_path)
            os.makedirs(temp_path)
        else:
            raise Exception(ex.message)

    # an empty visualization directory will not be put into the zipped bag file by ibun command,
    # so creating an empty visualization directory to be put into the zip file as done by the two
    # statements below does not work. However, if visualization directory has content to be
    # uploaded, it will work. This is to be implemented as part of the resource model in the future.
    # The following two statements are placeholders serving as reminder
    # to_file_name = '{res_id}/data/visualization/'.format(res_id=resource.short_id)
    # istorage.saveFile('', to_file_name, create_directory=True)

    # create resourcemetadata.xml in local directory and upload it to iRODS
    from_file_name = os.path.join(temp_path, 'resourcemetadata.xml')
    with open(from_file_name, 'w') as out:
        # resources that don't support file types this would write only resource level metadata
        # resource types that support file types this would write resource level metadata
        # as well as file type metadata
        out.write(resource.get_metadata_xml())
    to_file_name = os.path.join(resource.root_path, 'data', 'resourcemetadata.xml')
    istorage.saveFile(from_file_name, to_file_name, True)

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
            res_uri = u'{hs_url}/resource/{res_id}/data/contents/{file_name}'.format(
                hs_url=current_site_url,
                res_id=resource.short_id,
                file_name=f.short_path)
            ar = AggregatedResource(res_uri)
            ar._ore.isAggregatedBy = ag_url
            ar._dc.format = get_file_mime_type(os.path.basename(f.short_path))
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
            aggr_uri = u'{hs_url}/resource/{res_id}/data/contents/{map_file_path}#aggregation'
            aggr_uri = aggr_uri.format(
                hs_url=current_site_url,
                res_id=resource.short_id,
                map_file_path=logical_file.map_short_file_path)
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

    # create resourcemap.xml and upload it to iRODS
    from_file_name = os.path.join(temp_path, 'resourcemap.xml')
    with open(from_file_name, 'w') as out:
        out.write(xml_string)
    to_file_name = os.path.join(resource.root_path, 'data', 'resourcemap.xml')
    istorage.saveFile(from_file_name, to_file_name, False)

    # if the resource is a composite resource generate aggregation metadata
    # and map xml documents
    if resource.resource_type == "CompositeResource":
        resource.create_aggregation_xml_documents()

    res_coll = resource.root_path
    istorage.setAVU(res_coll, 'metadata_dirty', "false")
    shutil.rmtree(temp_path)
    return istorage


def create_bag(resource):
    """
    Modified to implement the new bagit workflow. The previous workflow was to create a bag from
    the current filesystem of the resource, then zip it up and add it to the resource. The new
    workflow is to delegate bagit and zip-up operations to iRODS, specifically, by executing an
    iRODS bagit rule to create bagit file hierarchy, followed by execution of an ibun command to
    zip up the bagit file hierarchy which is done asychronously as a celery task. This function
    only creates all bag files under resource collection in iRODS and set bag_modified iRODS AVU
    metadata to true so that the bag will be created or recreated on demand when it is being
    downloaded asychronously by a celery task.

    Parameters:
    :param resource: (subclass of AbstractResource) A resource to create a bag for.
    :return: the hs_core.models.Bags instance associated with the new bag.
    """
    create_bag_files(resource)

    # set bag_modified-true AVU pair for on-demand bagging.to indicate the resource bag needs to be
    # created when user clicks on download button
    resource.setAVU("bag_modified", True)

    # delete if there exists any bags for the resource
    resource.bags.all().delete()
    # link the zipped bag file in IRODS via bag_url for bag downloading
    b = Bags.objects.create(
        content_object=resource.baseresource,
        timestamp=resource.updated
    )

    return b


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
