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

    res_path = res_id
    bagname = 'bags/{res_id}.zip'.format(res_id=res_id)
    if resource.resource_federation_path:
        istorage = IrodsStorage('federated')
        res_path='{}/{}'.format(resource.resource_federation_path, res_path)
        bagname='{}/{}'.format(resource.resource_federation_path, bagname)
    else:
        istorage = IrodsStorage()
    # delete resource directory first to remove all generated bag-related files for the resource
    istorage.delete(res_path)

    # the resource bag may not exist due to on-demand bagging
    if istorage.exists(bagname):
        # delete the resource bag
        istorage.delete(bagname)

    # delete the bags table
    for bag in resource.bags.all():
        bag.delete()


def create_bag_files(resource, fed_zone_home_path=''):
    """
    create and update all files needed by bagit operation that is conducted on iRODS server; no bagit operation
    is performed, only files that will be included in the bag are created or updated.

    Parameters:
    :param resource: A resource whose files will be created or updated to be included in the resource bag.
    :param fed_zone_home_path: Optional, A passed-in non-empty value indicates the resource needs to be created
    in a federated zone rather than in the default hydroshare zone.
    :return: istorage, an IrodsStorage object,that will be used by subsequent operation to create a bag on demand as needed.
    """
    from hs_core.hydroshare.utils import current_site_url, get_file_mime_type
    DATE_FORMAT = "YYYY-MM-DDThh:mm:ssTZD"

    if fed_zone_home_path:
        istorage=IrodsStorage('federated')
    else:
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
    if fed_zone_home_path:
        to_file_name = '{fed_zone_home_path}/{rel_path}'.format(fed_zone_home_path=fed_zone_home_path, rel_path=to_file_name)
    istorage.saveFile(from_file_name, to_file_name, True)

    # make the resource map
    current_site_url = current_site_url()
    if fed_zone_home_path:
        hs_res_url = '{hs_url}/resource{zone}/{res_id}/data'.format(hs_url=current_site_url,
                                                                    zone=fed_zone_home_path,
                                                                    res_id=resource.short_id)
    else:
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
        if f.fed_resource_file_name_or_path:
            # move or copy the file under the user account to under local hydro proxy account in federated zone
            from_fname = f.fed_resource_file_name_or_path
            filename = from_fname.rsplit('/')[-1]
            res_path = os.path.join('{hs_url}/resource{zone}/{res_id}/data/contents/{file_name}'.format(
                hs_url=current_site_url, zone=resource.resource_federation_path, res_id=resource.short_id, file_name=filename))
        elif f.resource_file:
            filename = os.path.basename(f.resource_file.name)
            res_path = os.path.join('{hs_url}/resource/{res_id}/data/contents/{file_name}'.format(
                hs_url=current_site_url, res_id=resource.short_id, file_name=filename))
        elif f.fed_resource_file:
            filename = os.path.basename(f.fed_resource_file.name)
            res_path = os.path.join('{hs_url}/resource{zone}/{res_id}/data/contents/{file_name}'.format(
                hs_url=current_site_url, zone=resource.resource_federation_path, res_id=resource.short_id,
                file_name=filename))
        else:
            filename = ''
        if filename:
            resFiles.append(AggregatedResource(res_path))
            resFiles[n]._ore.isAggregatedBy = ag_url
            resFiles[n]._dc.format = get_file_mime_type(filename)

    #Add the resource files to the aggregation
    a.add_resource(resMetaFile)
    for f in resFiles:
        a.add_resource(f)

    # handle collection resource type
    # save cotained resource urls into resourcemap.xml
    if resource.resource_type == "CollectionResource" and resource.resources:
        for contained_res in resource.resources.all():
            contained_res_id = contained_res.short_id
            if contained_res.resource_federation_path:
                resource_map_url = '{hs_url}/resource{zone}/{res_id}/data/resourcemap.xml'.format(hs_url=current_site_url,
                                                                                            zone=contained_res.resource_federation_path,
                                                                                            res_id=contained_res_id)
            else:
                resource_map_url = '{hs_url}/resource/{res_id}/data/resourcemap.xml'.format(hs_url=current_site_url, res_id=contained_res_id)
            ar = AggregatedResource(resource_map_url)
            ar._ore.isAggregatedBy = ag_url
            ar._dc.format = "application/rdf+xml"
            a.add_resource(ar)

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
    if fed_zone_home_path:
        to_file_name = '{fed_zone_home_path}/{rel_path}'.format(fed_zone_home_path=fed_zone_home_path, rel_path=to_file_name)

    istorage.saveFile(from_file_name, to_file_name, False)

    shutil.rmtree(dest_prefix)
    return istorage


def create_bag_by_irods(resource_id, istorage = None):
    """
    create a resource bag on iRODS side by running the bagit rule followed by ibun zipping operation

    Parameters:
    :param resource_id: the resource uuid that is used to look for the resource to create the bag for.
           istorage: IrodsStorage object that is used to call irods bagit rule operation and zipping up operation

    :return: True if bag creation operation succeeds; False if there is an exception raised.
    """
    from hs_core.hydroshare.utils import get_resource_by_shortkey

    res = get_resource_by_shortkey(resource_id)
    is_exist = False
    bag_full_name = 'bags/{res_id}.zip'.format(res_id=resource_id)
    if res.resource_federation_path:
        if not istorage:
            istorage = IrodsStorage('federated')
        irods_bagit_input_path = os.path.join(res.resource_federation_path, resource_id)
        is_exist = istorage.exists(irods_bagit_input_path)
        bagit_input_path = "*BAGITDATA='{path}'".format(path=irods_bagit_input_path)
        bagit_input_resource = "*DESTRESC='{def_res}'".format(def_res=settings.HS_IRODS_LOCAL_ZONE_DEF_RES)
        bag_full_name = os.path.join(res.resource_federation_path, bag_full_name)
        bagit_files = [
                '{fed_path}/{res_id}/bagit.txt'.format(fed_path=res.resource_federation_path, res_id=resource_id),
                '{fed_path}/{res_id}/manifest-md5.txt'.format(fed_path=res.resource_federation_path, res_id=resource_id),
                '{fed_path}/{res_id}/tagmanifest-md5.txt'.format(fed_path=res.resource_federation_path, res_id=resource_id),
                '{fed_path}/bags/{res_id}.zip'.format(fed_path=res.resource_federation_path, res_id=resource_id)
        ]
    else:
        if not istorage:
            istorage = IrodsStorage()
        is_exist = istorage.exists(resource_id)
        irods_dest_prefix = "/" + settings.IRODS_ZONE + "/home/" + settings.IRODS_USERNAME
        irods_bagit_input_path = os.path.join(irods_dest_prefix, resource_id)
        bagit_input_path = "*BAGITDATA='{path}'".format(path=irods_bagit_input_path)
        bagit_input_resource = "*DESTRESC='{def_res}'".format(def_res=settings.IRODS_DEFAULT_RESOURCE)
        bagit_files = [
                '{res_id}/bagit.txt'.format(res_id=resource_id),
                '{res_id}/manifest-md5.txt'.format(res_id=resource_id),
                '{res_id}/tagmanifest-md5.txt'.format(res_id=resource_id),
                'bags/{res_id}.zip'.format(res_id=resource_id)
        ]


    # only proceed when the resource is not deleted potentially by another request when being downloaded
    if is_exist:
        # call iRODS bagit rule here
        bagit_rule_file = getattr(settings, 'IRODS_BAGIT_RULE', 'hydroshare/irods/ruleGenerateBagIt_HS.r')

        try:
            # call iRODS run and ibun command to create and zip the bag,
            # ignore SessionException for now as a workaround which could be raised
            # from potential race conditions when multiple ibun commands try to create the same zip file or
            # the very same resource gets deleted by another request when being downloaded
            istorage.runBagitRule(bagit_rule_file, bagit_input_path, bagit_input_resource)
            istorage.zipup(irods_bagit_input_path, bag_full_name)
            return True
        except SessionException:
            # if an exception occurs, delete incomplete files potentially being generated by
            # iRODS bagit rule and zipping operations
            for fname in bagit_files:
                if istorage.exists(fname):
                    istorage.delete(fname)
            return False


def create_bag(resource, fed_zone_home_path=''):
    """
    Modified to implement the new bagit workflow. The previous workflow was to create a bag from the current filesystem
    of the resource, then zip it up and add it to the resource. The new workflow is to delegate bagit and zip-up
    operations to iRODS, specifically, by executing an iRODS bagit rule to create bagit file hierarchy, followed by
    execution of an ibun command to zip up the bagit file hierarchy.

    Note, this procedure may take awhile.  It is highly advised that it be deferred to a Celery task.

    Parameters:
    :param resource: (subclass of AbstractResource) A resource to create a bag for.
           fed_zone_home_path: default is empty indicating the resource bag should be created and
                               stored in the default hydroshare zone; a non-empty string value
                               indicates the absolute logical home path for the federated zone where
                               the new created bag should be stored in
    :return: the hs_core.models.Bags instance associated with the new bag.
    """

    istorage = create_bag_files(resource, fed_zone_home_path)

    # set bag_modified-true AVU pair for on-demand bagging.to indicate the resource bag needs to be created when user clicks on download button
    if fed_zone_home_path:
        to_coll_name = '{fed_zone_home_path}/{rel_path}'.format(fed_zone_home_path=fed_zone_home_path, rel_path=resource.short_id)
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
