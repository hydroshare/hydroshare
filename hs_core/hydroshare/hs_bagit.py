import arrow
import os
import shutil

from foresite import *
from rdflib import URIRef, Namespace

from mezzanine.conf import settings

from hs_core.models import Bags, ResourceFile
from django_irods.storage import IrodsStorage

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
    from . import utils as hs_core_utils
    DATE_FORMAT = "YYYY-MM-DDThh:mm:ssTZD"
    istorage=IrodsStorage()

    dest_prefix = getattr(settings, 'BAGIT_TEMP_LOCATION', '/tmp/hydroshare/')
    bagit_path = os.path.join(dest_prefix, resource.short_id, arrow.get(resource.updated).format("YYYY.MM.DD.HH.mm.ss"))

    for d in (dest_prefix, bagit_path):
        try:
            os.makedirs(d)
        except:
            shutil.rmtree(d)
            os.makedirs(d)

    # create visualization directory and upload all files under it as needed in iRODS to be part of bag
    to_file_name = '{res_id}/data/visualization/'.format(res_id=resource.short_id)
    istorage.saveFile('', to_file_name, True)

    # create resourcemetadata.xml and upload it to iRODS
    from_file_name = '{path}/resourcemetadata.xml'.format(path=bagit_path)
    with open(from_file_name, 'w') as out:
        out.write(resource.metadata.get_xml())

    to_file_name = '{res_id}/data/resourcemetadata.xml'.format(res_id=resource.short_id)
    istorage.saveFile(from_file_name, to_file_name, False)

    # make the resource map
    current_site_url = hs_core_utils.current_site_url()
    hs_res_url = '{hs_url}/resource/{res_id}/data'.format(hs_url=current_site_url, res_id=resource.short_id)
    metadata_url = os.path.join(hs_res_url, 'resourcemetadata.xml')
    res_map_url = os.path.join(hs_res_url, 'resourcemap.xml')

    ##make the resource map:
    # utils.namespaces['hsterms'] = Namespace('{hs_url}/hsterms/'.format(hs_url=current_site_url))
    # utils.namespaceSearchOrder.append('hsterms')
    utils.namespaces['citoterms'] = Namespace('http://purl.org/spar/cito/')
    utils.namespaceSearchOrder.append('citoterms')

    ag_url = os.path.join(hs_res_url, 'resourcemap.xml#aggregation')
    a = Aggregation(ag_url)

    #Set properties of the aggregation
    a._dc.title = resource.title
    a._dcterms.created = arrow.get(resource.updated).format(DATE_FORMAT)
    a._dcterms.type = resource._meta.object_name
    a._citoterms.isDocumentedBy = metadata_url
    a._ore.isDescribedBy = res_map_url

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
        resFiles.append(AggregatedResource(os.path.join('{hs_url}/resource/{res_id}/data/contents'.format(
            hs_url=current_site_url, res_id=resource.short_id))))

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

    # create resourcemap.xml and upload it to iRODS
    from_file_name = '{path}/resourcemap.xml'.format(path=bagit_path)
    with open(from_file_name, 'w') as out:
        out.write(xml_string)
    to_file_name = '{res_id}/data/resourcemap.xml'.format(res_id=resource.short_id)
    istorage.saveFile(from_file_name, to_file_name, False)

    # call iRODS bagit rule here
    irods_dest_prefix = "/" + settings.IRODS_ZONE + "/home/" + settings.IRODS_USERNAME
    irods_bagit_input_path = os.path.join(irods_dest_prefix, resource.short_id)
    bagit_input = "*BAGITDATA='{path}'".format(path=irods_bagit_input_path)
    istorage.runBagitRule('ruleGenerateBagIt_HS.r', bagit_input)

    # call iRODS ibun command to zip the bag
    istorage.zipup(irods_bagit_input_path, 'bags/{res_id}.zip'.format(res_id=resource.short_id))

    # link the zipped bag file in IRODS via bag_url for bag downloading
    b = Bags.objects.create(
        content_object=resource,
        bag_url="/django_irods/download/?path=bags/{res_id}.zip".format(res_id=resource.short_id),
        timestamp=resource.updated
    )

    shutil.rmtree(bagit_path)

    return b
