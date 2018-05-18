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

def create_bag(resource):

    resource.setAVU("bag_modified", True)

    checksums = ['md5', 'sha256']

    # generate remote-file-mainfest for fetch.txt
    # generate metatdata json for bag-info.txt
    remote_file_manifest_json = get_remote_file_manifest(resource)
    metadata_json = get_metadata_json(resource)

    tmpdir = os.path.join(settings.TEMP_FILE_DIR, uuid4().hex, resource.short_id)
    os.makedirs(tmpdir)

    # create the remote manifest and metadata files
    remote_manifest_file = os.path.join(tmpdir, 'remote-file-manifest.json')
    with open(remote_manifest_file, 'w') as out:
        out.write(remote_file_manifest_json)

    metadata_file = os.path.join(tmpdir, 'metadata.json')
    with open(metadata_file, 'w') as out:
        out.write(metadata_json)

    bagdir = os.path.join(tmpdir, "bag")
    os.makedirs(bagdir)

    # make the bdbag and create a zip archive
    bdb.make_bag(bagdir, checksums, False, False, False, None, metadata_file, remote_manifest_file, 'config/bdbag.json')
    zipfile = bdb.archive_bag(bagdir, "zip")

    # save the zipped bag to iRODS for retrieval upon download request
    istorage = resource.get_irods_storage()
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
