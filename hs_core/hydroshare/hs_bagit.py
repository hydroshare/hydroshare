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
from django_irods.storage import IrodsStorage


class HsBagitException(Exception):
    pass


def delete_bag(resource):
    """
    delete the resource bag

    Parameters:
    :param resource: the resource to delete the bag for.
    :return: none
    """
    res_id = resource.short_id

    # TODO: resource.get_storage would be easier to remember. 
    istorage = resource.get_irods_storage()

    # delete resource directory first to remove all generated bag-related files for the resource
    # TODO: this will cause a cascade delete problem with the resource. 
    # TODO: We need to revise resource deletion  or decide not to do this. 
    if istorage.exists(resource.root_path): 
        istorage.delete(resource.root_path)

    if istorage.exists(resource.bag_path):
        istorage.delete(resource.bag_path)

    # delete the bags table
    # TODO: what is this for? Why were extra bags created in the first place?
    for bag in resource.bags.all():
        bag.delete()


# TODO: remove the federated zone home path; it is determined by the resource 
def create_bag_files(resource, fed_zone_home_path=''):
    """
    create and update files needed by bagit operation that is conducted on iRODS server; no bagit
    operation is performed, only files that will be included in the bag are created or updated.

    Parameters:
    :param resource: A resource whose files will be created or updated to be included in the
    resource bag.
    :param fed_zone_home_path: Optional, A passed-in non-empty value that indicates that the
    resource needs to be created in a federated zone rather than in the default hydroshare zone.
    :return: istorage, an IrodsStorage object that will be used by subsequent operation to
    create a bag on demand as needed.
    """
    from hs_core.hydroshare.utils import current_site_url, get_file_mime_type

    istorage = resource.get_irods_storage()

    # has to make bagit_path unique even for the same resource with same update time
    # to accommodate asynchronous multiple file move operations for the same resource
    # TODO: This should be a method in Resource. 
    # TODO: This disagrees with the permanent bag storage path. 
    temp_bagit_path = os.path.join(getattr(settings, 'IRODS_ROOT', '/tmp'), uuid4().hex)

    # TODO: this causes a potential race condition if two people try to run the bagit code
    # TODO: at the same time. Encapsulate in Resource. 

    try:
        os.makedirs(temp_bagit_path)
    except OSError as ex:
        if ex.errno == errno.EEXIST:
            shutil.rmtree(temp_bagit_path)
            os.makedirs(temp_bagit_path)
        else:
            raise Exception(ex.message)

    # an empty visualization directory will not be put into the zipped bag file by ibun command,
    # so creating an empty visualization directory to be put into the zip file as done by the two
    # statements below does not work. However, if visualization directory has content to be
    # uploaded, it will work. This is to be implemented as part of the resource model in the future.
    # The following two statements are placeholders serving as reminder
    # to_file_name = '{res_id}/data/visualization/'.format(res_id=resource.short_id)
    # istorage.saveFile('', to_file_name, create_directory=True)

    # create resourcemetadata.xml and upload it to iRODS
    from_file_name = os.path.join(temp_bagit_path, 'resourcemetadata.xml')
    with open(from_file_name, 'w') as out:
        out.write(resource.metadata.get_xml())

    # TODO: this conflicts with the location of resourcemetadata.xml in other files. 
    # TODO: I conclude that it is a temporary location. 
    # TODO: we need an arbitrary hashed filename to avoid race conditions. 
    to_file_name = os.path.join(resource.root_path, 'data', 'resourcemetadata.xml')
    istorage.saveFile(from_file_name, to_file_name, True)

    # make the resource map
    # This is the URL of the whole site. 
    # TODO: move this to BaseResource. 
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

    # Create a description of the content file and add it to the aggregation
    files = ResourceFile.objects.filter(object_id=resource.id)
    resFiles = []
    for n, f in enumerate(files):
        prefix_str = 'data/contents/'
        prefix_len = len(prefix_str)

        file_name_with_rel_path = ''
        # TODO: refactor to utilize root path name 
        # move or copy the file under the user account to under local hydro proxy account
        # in federated zone
        idx = f.resource.root_path.find(prefix_str)
        if idx >= 0:
            file_name_with_rel_path = f.fed_resource_file_name_or_path[idx+prefix_len:]

        if file_name_with_rel_path:
            res_path = '{hs_url}/resource/{res_id}/data/contents/{file_name}'.format(
                hs_url=current_site_url,
                res_id=resource.short_id,
                file_name=file_name_with_rel_path)
            resFiles.append(AggregatedResource(res_path))
            resFiles[n]._ore.isAggregatedBy = ag_url
            resFiles[n]._dc.format = get_file_mime_type(os.path.basename(file_name_with_rel_path))

    # Add the resource files to the aggregation
    a.add_resource(resMetaFile)
    for f in resFiles:
        a.add_resource(f)

    # handle collection resource type
    # save cotained resource urls into resourcemap.xml
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
        '<ore:aggregates rdf:resource="%s"/>\n' % resource.metadata.type.url, '')

    # create resourcemap.xml and upload it to iRODS
    from_file_name = os.path.join(bagit_path, 'resourcemap.xml')
    with open(from_file_name, 'w') as out:
        out.write(xml_string)
    to_file_name = os.path.join(resource.short_id, 'data', 'resourcemap.xml')
    if fed_zone_home_path:
        to_file_name = '{fed_zone_home_path}/{rel_path}'.format(
            fed_zone_home_path=fed_zone_home_path,
            rel_path=to_file_name)

    istorage.saveFile(from_file_name, to_file_name, False)

    shutil.rmtree(bagit_path)
    return istorage


def create_bag(resource, fed_zone_home_path=''):
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
           fed_zone_home_path: default is empty indicating the resource bag should be created and
                               stored in the default hydroshare zone; a non-empty string value
                               indicates the absolute logical home path for the federated zone where
                               the new created bag should be stored in
    :return: the hs_core.models.Bags instance associated with the new bag.
    """

    istorage = create_bag_files(resource, fed_zone_home_path)

    # set bag_modified-true AVU pair for on-demand bagging.to indicate the resource bag needs to be
    # created when user clicks on download button
    if fed_zone_home_path:
        to_coll_name = '{fed_zone_home_path}/{rel_path}'.format(
            fed_zone_home_path=fed_zone_home_path,
            rel_path=resource.short_id)
    else:
        to_coll_name = resource.short_id

    istorage.setAVU(to_coll_name, "bag_modified", "true")

    istorage.setAVU(to_coll_name, "isPublic", str(resource.raccess.public))

    istorage.setAVU(to_coll_name, "resourceType", resource._meta.object_name)

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
