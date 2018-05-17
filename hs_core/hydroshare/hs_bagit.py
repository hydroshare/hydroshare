import os
import shutil
import errno
import tempfile
import mimetypes
import zipfile
import hashlib

from uuid import uuid4

from foresite import utils, Aggregation, AggregatedResource, RdfLibSerializer
from rdflib import Namespace, URIRef

import bagit
from mezzanine.conf import settings
from hs_core.models import Bags, ResourceFile

from bdbag import bdbag_api as bdb, get_typed_exception, DEFAULT_CONFIG_FILE, VERSION
from bdbag.fetch.auth.keychain import DEFAULT_KEYCHAIN_FILE

from django.conf import settings

from minid_client import minid_client_api as mca

import json

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
    resMetaFile._dc.title = "Dublin Core science metadata document describing the CommonsShare " \
                            "resource"
    resMetaFile._citoterms.documents = ag_url
    resMetaFile._ore.isAggregatedBy = ag_url
    resMetaFile._dc.format = "application/rdf+xml"

    # Create a description of the content file and add it to the aggregation
    files = ResourceFile.objects.filter(object_id=resource.id)
    resFiles = []
    for n, f in enumerate(files):
        res_uri = u'{hs_url}/resource/{res_id}/data/contents/{file_name}'.format(
            hs_url=current_site_url,
            res_id=resource.short_id,
            file_name=f.short_path)
        resFiles.append(AggregatedResource(res_uri))
        resFiles[n]._ore.isAggregatedBy = ag_url
        resFiles[n]._dc.format = get_file_mime_type(os.path.basename(f.short_path))

    # Add the resource files to the aggregation
    a.add_resource(resMetaFile)
    for f in resFiles:
        a.add_resource(f)

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

    res_coll = resource.root_path
    istorage.setAVU(res_coll, 'metadata_dirty', "false")
    shutil.rmtree(temp_path)
    return istorage

def create_bag(resource):
    
    create_bag_files(resource)
    resource.setAVU("bag_modified", True)

    checksums = ['md5', 'sha256']

    # generate remote-file-mainfest for fetch.txt
    # generate metatdata json for bag-info.txt

    remote_file_manifest_json = get_remote_file_manifest(resource)
    metadata_json = get_metadata_json(resource)

    tmpdir = os.path.join(settings.TEMP_FILE_DIR, uuid4().hex, resource.short_id)
    os.makedirs(tmpdir)

    remote_manifest_file = os.path.join(tmpdir, 'remote-file-manifest.json')
    with open(remote_manifest_file, 'w') as out:
        out.write(remote_file_manifest_json)

    metadata_file = os.path.join(tmpdir, 'metadata.json')
    with open(metadata_file, 'w') as out:
        out.write(metadata_json)

    bagdir = os.path.join(tmpdir, "bag")
    os.makedirs(bagdir)

    bdb.make_bag(bagdir, checksums, False, False, False, None, metadata_file, remote_manifest_file, 'config/bdbag.json')

    istorage = resource.get_irods_storage()

    zipfile = bdb.archive_bag(bagdir, "zip")

    bag_full_name = 'bags/{res_id}.zip'.format(res_id=resource.short_id)
    irods_dest_prefix = "/" + settings.IRODS_ZONE + "/home/" + settings.IRODS_USERNAME
    destbagfile = os.path.join(irods_dest_prefix, bag_full_name)

    istorage.saveFile(zipfile, destbagfile, True)

    # delete if there exists any bags for the resource
    resource.bags.all().delete()
    # link the zipped bag file in IRODS via bag_url for bag downloading
    b = Bags.objects.create(
        content_object=resource.baseresource,
        timestamp=resource.updated
    )

    return b


def get_remote_file_manifest(resource):
    json_data = ''
    for f in ResourceFile.objects.filter(object_id=resource.id):
        data = {}
        irods_file_name = resource.short_id + "/data/contents/" + f.file_name
        irods_dest_prefix = "/" + settings.IRODS_ZONE + "/home/" + settings.IRODS_USERNAME
        irods_server_prefix = settings.IRODS_HOST + ':' + settings.IRODS_PORT
        irods_file_url = 'irods://' + irods_server_prefix +  irods_dest_prefix + "/" + irods_file_name
        istorage = resource.get_irods_storage()

        tmpdir = os.path.join(settings.TEMP_FILE_DIR, uuid4().hex)
        tmpfile = os.path.join(tmpdir, f.file_name)

        os.makedirs(tmpdir)

        srcfile = os.path.join(irods_dest_prefix, irods_file_name)
        istorage.getFile(srcfile, tmpfile)
        checksum_md5 = mca.compute_checksum(tmpfile, hashlib.md5())
        checksum_sha256 = mca.compute_checksum(tmpfile, hashlib.sha256())
        data['url'] = irods_file_url
        data['length'] = f.size
        data['filename'] = f.file_name
        data['md5'] = checksum_md5
        data['sha256'] = checksum_sha256
        json_data += json.dumps(data)

    return json_data

def get_metadata_json(resource):
    data = {}
    data['BagIt-Profile-Identifier'] = "https://raw.githubusercontent.com/fair-research/bdbag/master/profiles/bdbag-profile.json"
    data['External-Description'] = "CommonsShare BDBag for resource " + resource.short_id
    data['Arbitrary-Metadata-Field'] = "TBD Arbitrary metadata field"

    return json.dumps(data)
