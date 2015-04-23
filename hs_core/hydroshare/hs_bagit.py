import arrow
import bagit
from django.core.files import File
import os
import shutil
from hs_core.models import Bags, ResourceFile

from mezzanine.conf import settings
import importlib
import zipfile
from foresite import *
from rdflib import URIRef, Namespace

def make_zipfile(output_filename, source_dir):
    """
    Create a zipfile recursively from a source directory, saving the relative path of all objects.

    Parameters:
    :param output_filename: (str) The output filename
    :param source_dir: (str) The source directory to zip
    """
    relroot = os.path.abspath(os.path.join(source_dir, os.pardir))
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zip:
        for root, dirs, files in os.walk(source_dir):
            # add directory (needed for empty dirs)
            zip.write(root, os.path.relpath(root, relroot))
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename): # regular files only
                    arcname = os.path.join(os.path.relpath(root, relroot), file)
                    zip.write(filename, arcname)

def create_bag(resource):
    """
    Create a bag from the current filesystem of the resource, then zip it up and add it to the resource.

    Note, this procedure may take awhile.  It is highly advised that it be deferred to a Celery task.

    Parameters:
    :param resource: (subclass of AbstractResource) A resource to create a bag for.

    :return: the hs_core.models.Bags instance associated with the new bag.
    """
    from . import utils as hs_core_utils
    DATE_FORMAT = "YYYY-MM-DDThh:mm:ssTZD"

    dest_prefix = getattr(settings, 'BAGIT_TEMP_LOCATION', '/tmp/hydroshare/')
    bagit_path = os.path.join(dest_prefix, resource.short_id, arrow.get(resource.updated).format("YYYY.MM.DD.HH.mm.ss"))
    visualization_path = os.path.join(bagit_path, 'visualization')
    contents_path = os.path.join(bagit_path, 'contents')

    for d in (dest_prefix, bagit_path, visualization_path, contents_path):
        try:
            os.makedirs(d)
        except:
            shutil.rmtree(d)
            os.makedirs(d)

    for f in resource.files.all():
        rfile_name = f.resource_file.name.split('/', 1)[1] # truncate short_id directory name
        opath = os.path.join(contents_path, rfile_name).rsplit('/', 1)[0]
        if opath != contents_path:
            try:
                os.makedirs(opath)
            except Exception as e:
                print e

        with open(os.path.join(contents_path, rfile_name), 'w+b') as out:
            for chunk in f.resource_file.chunks():
                out.write(chunk)

    with open(bagit_path + '/resourcemetadata.xml', 'w') as out:
        out.write(resource.metadata.get_xml())


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
    with open(bagit_path + '/resourcemap.xml', 'w') as out:
        out.write(xml_string)

    bagit.make_bag(bagit_path, checksum=['md5'])

    zf = os.path.join(dest_prefix, resource.short_id) + ".zip"
    make_zipfile(output_filename=zf, source_dir=bagit_path)
    b = Bags.objects.create(
        content_object=resource,
        bag=File(open(zf)),
        timestamp=resource.updated
    )

    os.unlink(zf)
    shutil.rmtree(bagit_path)

    return b
