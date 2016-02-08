import arrow
import os
import shutil
import errno
import tempfile
import mimetypes
import zipfile

from foresite import utils, Aggregation, AggregatedResource, RdfLibSerializer
from rdflib import Namespace, URIRef

import bagit

from mezzanine.conf import settings

from hs_core.models import Bags, ResourceFile
from django_irods.storage import IrodsStorage
from django_irods.icommands import SessionException


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
    istorage = IrodsStorage()

    # delete resource directory first to remove all generated bag-related files for the resource
    istorage.delete(res_id)

    # the resource bag may not exist due to on-demand bagging
    bagname = 'bags/{res_id}.zip'.format(res_id=res_id)
    if istorage.exists(bagname):
        # delete the resource bag
        istorage.delete(bagname)

    # delete the bags table
    for bag in resource.bags.all():
        bag.delete()


def create_bag_files(resource):
    """
    create and update all files needed by bagit operation that is conducted on iRODS server; no bagit operation
    is performed, only files that will be included in the bag are created or updated.

    Parameters:
    :param resource: A resource whose files will be created or updated to be included in the resource bag.

    :return: istorage, an IrodsStorage object,that will be used by subsequent operation to create a bag on demand as needed.
    """
    from . import utils as hs_core_utils
    DATE_FORMAT = "YYYY-MM-DDThh:mm:ssTZD"
    istorage=IrodsStorage()

    dest_prefix = getattr(settings, 'BAGIT_TEMP_LOCATION', '/tmp/hydroshare/')
    bagit_path = os.path.join(dest_prefix, resource.short_id, arrow.get(resource.updated).format("YYYY.MM.DD.HH.mm.ss"))

    for d in (dest_prefix, bagit_path):
        try:
            os.makedirs(d)
        except OSError as ex:
            if ex.errno == errno.EEXIST:
                shutil.rmtree(d)
                os.makedirs(d)
            else:
                raise Exception(ex.message)

    # an empty visualization directory will not be put into the zipped bag file by ibun command, so creating an empty
    # visualization directory to be put into the zip file as done by the two statements below does not work. However,
    # if visualization directory has content to be uploaded, it will work. This is to be implemented as part of the
    # resource model in the future. The following two statements are placeholders serving as reminder
    # to_file_name = '{res_id}/data/visualization/'.format(res_id=resource.short_id)
    # istorage.saveFile('', to_file_name, create_directory=True)

    # create resourcemetadata.xml and upload it to iRODS
    from_file_name = '{path}/resourcemetadata.xml'.format(path=bagit_path)
    with open(from_file_name, 'w') as out:
        out.write(resource.metadata.get_xml())

    to_file_name = '{res_id}/data/resourcemetadata.xml'.format(res_id=resource.short_id)
    istorage.saveFile(from_file_name, to_file_name, True)

    # make the resource map
    current_site_url = hs_core_utils.current_site_url()
    hs_res_url = '{hs_url}/resource/{res_id}/data'.format(hs_url=current_site_url, res_id=resource.short_id)
    metadata_url = os.path.join(hs_res_url, 'resourcemetadata.xml')
    res_map_url = os.path.join(hs_res_url, 'resourcemap.xml')

    ##make the resource map:
    utils.namespaces['citoterms'] = Namespace('http://purl.org/spar/cito/')
    utils.namespaceSearchOrder.append('citoterms')

    ag_url = os.path.join(hs_res_url, 'resourcemap.xml#aggregation')
    a = Aggregation(ag_url)

    #Set properties of the aggregation
    a._dc.title = resource.metadata.title.value
    a._dcterms.type = URIRef(resource.metadata.type.url)
    a._citoterms.isDocumentedBy = metadata_url
    a._ore.isDescribedBy = res_map_url

    res_type_aggregation = AggregatedResource(resource.metadata.type.url)
    res_type_aggregation._rdfs.label = resource._meta.verbose_name
    res_type_aggregation._rdfs.isDefinedBy = current_site_url + "/terms"

    a.add_resource(res_type_aggregation)

    #Create a description of the metadata document that describes the whole resource and add it to the aggregation
    resMetaFile = AggregatedResource(metadata_url)
    resMetaFile._dc.title = "Dublin Core science metadata document describing the HydroShare resource"
    resMetaFile._citoterms.documents = ag_url
    resMetaFile._ore.isAggregatedBy = ag_url
    resMetaFile._dc.format = "application/rdf+xml"


    #Create a description of the content file and add it to the aggregation
    files = ResourceFile.objects.filter(object_id=resource.id)
    resFiles = []
    for n, f in enumerate(files):
        filename = os.path.basename(f.resource_file.name)
        resFiles.append(AggregatedResource(os.path.join('{hs_url}/resource/{res_id}/data/contents/{file_name}'.format(
            hs_url=current_site_url, res_id=resource.short_id, file_name=filename))))

        resFiles[n]._ore.isAggregatedBy = ag_url
        resFiles[n]._dc.format = hs_core_utils.get_file_mime_type(filename)

    #Add the resource files to the aggregation
    a.add_resource(resMetaFile)
    for f in resFiles:
        a.add_resource(f)

    #Register a serializer with the aggregation.  The registration creates a new ResourceMap, which needs a URI
    serializer = RdfLibSerializer('xml')
    resMap = a.register_serialization(serializer, res_map_url)
    resMap._dc.identifier = resource.short_id  #"resource_identifier"

    #Fetch the serialization
    remdoc = a.get_serialization()

    # change the namespace for the 'creator' element from 'dcterms' to 'dc'
    xml_string = remdoc.data.replace('dcterms:creator', 'dc:creator')

    # delete this extra element
    #<ore:aggregates rdf:resource="[hydroshare domain]/terms/[Resource class name]"/>
    xml_string = xml_string.replace('<ore:aggregates rdf:resource="%s"/>\n' % resource.metadata.type.url, '')

    # create resourcemap.xml and upload it to iRODS
    from_file_name = os.path.join(bagit_path, 'resourcemap.xml')
    with open(from_file_name, 'w') as out:
        out.write(xml_string)
    to_file_name = os.path.join(resource.short_id, 'data', 'resourcemap.xml')
    istorage.saveFile(from_file_name, to_file_name, False)

    shutil.rmtree(bagit_path)

    return istorage


def create_bag_by_irods(resource_id, istorage = None):
    """
    create a resource bag on iRODS side by running the bagit rule followed by ibun zipping operation

    Parameters:
    :param resource_id: the resource uuid that is used to look for the resource to create the bag for.
           istorage: IrodsStorage object that is used to call irods bagit rule operation and zipping up operation

    :return: none
    """
    if not istorage:
        istorage = IrodsStorage()

    # only proceed when the resource is not deleted potentially by another request when being downloaded
    if istorage.exists(resource_id):
        # call iRODS bagit rule here
        irods_dest_prefix = "/" + settings.IRODS_ZONE + "/home/" + settings.IRODS_USERNAME
        irods_bagit_input_path = os.path.join(irods_dest_prefix, resource_id)
        bagit_input_path = "*BAGITDATA='{path}'".format(path=irods_bagit_input_path)
        bagit_input_resource = "*DESTRESC='{def_res}'".format(def_res=settings.IRODS_DEFAULT_RESOURCE)
        bagit_rule_file = getattr(settings, 'IRODS_BAGIT_RULE', 'hydroshare/irods/ruleGenerateBagIt_HS.r')

        try:
            # call iRODS run and ibun command to create and zip the bag,
            # ignore SessionException for now as a workaround which could be raised
            # from potential race conditions when multiple ibun commands try to create the same zip file or
            # the very same resource gets deleted by another request when being downloaded
            istorage.runBagitRule(bagit_rule_file, bagit_input_path, bagit_input_resource)
            istorage.zipup(irods_bagit_input_path, 'bags/{res_id}.zip'.format(res_id=resource_id))
        except SessionException:
            pass


def create_bag(resource):
    """
    Modified to implement the new bagit workflow. The previous workflow was to create a bag from the current filesystem
    of the resource, then zip it up and add it to the resource. The new workflow is to delegate bagit and zip-up
    operations to iRODS, specifically, by executing an iRODS bagit rule to create bagit file hierarchy, followed by
    execution of an ibun command to zip up the bagit file hierarchy.

    Note, this procedure may take awhile.  It is highly advised that it be deferred to a Celery task.

    Parameters:
    :param resource: (subclass of AbstractResource) A resource to create a bag for.

    :return: the hs_core.models.Bags instance associated with the new bag.
    """

    istorage = create_bag_files(resource)

    # set bag_modified-true AVU pair for on-demand bagging.to indicate the resource bag needs to be created when user clicks on download button
    istorage.setAVU(resource.short_id, "bag_modified", "true")

    istorage.setAVU(resource.short_id, "isPublic", str(resource.raccess.public))

    istorage.setAVU(resource.short_id, "resourceType", resource._meta.object_name)

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
    #import pdb; pdb.set_trace()
    tmpdir = None
    unpacked_bag_path = None

    try:
        if not os.path.exists(bag_path):
            raise HsBagitException('Bag does not exist')
        if os.path.isdir(bag_path):
            unpacked_bag_path = bag_path
        else:
            mtype = mimetypes.guess_type(bag_path)
            if mtype[0] != 'application/zip':
                msg = "Expected bag to have MIME type application/zip, but it has {0} instead.".format(mtype[0])
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
