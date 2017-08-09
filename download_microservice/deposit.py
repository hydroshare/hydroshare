import datetime
import hashlib
from collections import deque

import flask
from irods.keywords import FORCE_FLAG_KW

from irods_utils import get_irods_session, join_paths

app = flask.Flask(__name__)


def update_manifest(session, perm_path, tmp_path, filename_hashes):
    """
    Given a set of changes to files indicated by filename_hashes,
      read in the current manifest from perm_path
      and create a new manifest in tmp_path merging old data, with new updates.
    """
    perm_manifest_path = join_paths(perm_path, 'manifest-md5.txt')
    try:
        session.data_objects.get(perm_manifest_path)
        exists = True
    except:
        exists = False
    if exists:
        app.logger.debug('Reading stored current manifest')
        # Read in any existing manifest if available.
        with session.data_objects.open(perm_manifest_path, 'r') as manifest_fp:
            while True:
                line = manifest_fp.readline().decode('utf-8').strip()
                app.logger.debug('Read manifest line: "{}"'.format(line))
                if not line:
                    break
                # TODO: Add more careful parsing of previously stored here
                digest, filename = line.split(' ')
                if filename not in filename_hashes:
                    filename_hashes.update({filename: digest})

    # Write combined existing manifest + new entries to manifest in tmp
    #   location.
    tmp_manifest_path = join_paths(tmp_path, 'manifest-md5.txt')
    tmp_manifest_do = session.data_objects.create(tmp_manifest_path)
    with tmp_manifest_do.open('w') as manifest_fp:
        for fn, md5 in filename_hashes.items():
            line = '{} {}\n'.format(md5, fn)
            manifest_fp.write(bytes(line, encoding='utf-8'))
    return filename_hashes


def translate_path(old_base, new_base, full_path):
    """
    Given ``full_path`` as a sub structure of ``old_base``,
      return a new path as a subpath of ``new_base`` rather than ``old_base``.
    """
    if not full_path.startswith(old_base):
        raise
    return join_paths(new_base, full_path[len(old_base):])


def merge_to_resource(session, tmp_path, perm_path, dryrun=False):
    """
    Walk the temporariy path, and compare it to the permanent path.
        Create new collections and move new/updated data objects.

    If dryrun is True do not actually update permanent resource.
    """
    if not session.collections.exists(perm_path):
        # This is a new collection. We need to create the destinations.
        app.logger.debug('Creating collection: {}'.format(perm_path))
        if not dryrun:
            session.collections.create(perm_path)
    else:
        app.logger.debug('Collection already exists: {}'.format(perm_path))

    tmp_root = session.collections.get(tmp_path)
    app.logger.debug('Merging: {} and {}'.format(perm_path, tmp_path))
    for col, _, data_objects in tmp_root.walk():
        perm_col_path = translate_path(tmp_path, perm_path, col.path)
        if not session.collections.exists(perm_col_path):
            app.logger.debug('Creating collection: {}'.format(perm_col_path))
            if not dryrun:
                session.collections.create(perm_col_path)
        for tmp_do in data_objects:
            # Can't move from full DO path -> DO path.
            #   So, instead move DO path -> parent collection
            dest_path = translate_path(tmp_path, perm_path,
                                       tmp_do.path)
            app.logger.debug('Moving do: {} -> {}'.format(tmp_do.path,
                                                          dest_path))
            if not dryrun:
                # There are currently issues with the .move API.
                tmp_do.manager.copy(tmp_do.path, dest_path,
                                    options={FORCE_FLAG_KW: ''})


def upload_files(short_key):
    """
    Flask view. POST files(s) to Hydroshare resource ``short_key``.
        These files will be merged with the current set of files and the hash
        manifest will be updated accordingly.
    """
    app.logger.info('Starting upload to {}'.format(short_key))
    session = get_irods_session()

    collection_full_path = join_paths(session.base_path, short_key)
    app.logger.debug('Working with {}'.format(collection_full_path))

    # Do not upload directly into a resource.
    #  Instead, upload into temporary space and (quickly) merge via move.
    #  This will improve usabilitiy as locks should not be held long.
    now_str = datetime.datetime.now().strftime('%Y-%m-%d-%H-%m-%S-%f')
    tmp_upload_path = join_paths(session.upload_path, now_str)

    if session.collections.exists(tmp_upload_path):
        # This should be impossible given the timestamp. But lets be defensive.
        raise
    session.collections.create(tmp_upload_path)
    session.collections.create(join_paths(tmp_upload_path, '/data'))

    # Perform chunked read from clients,
    #   writing to iRODS temp upload path and creating hashes as we go.
    hashes = {}
    for fn in flask.request.files:
        md5_hash = hashlib.md5()
        # TODO: Over quota? => Bail. Or is there a way to check this earlier?
        stream = flask.request.files[fn].stream
        tmp_file_path = join_paths(join_paths(tmp_upload_path, '/data'), fn)
        data_object = session.data_objects.create(tmp_file_path)
        with data_object.open('w') as do_fp:
            chunked_buf = deque()
            while True:
                chunk = stream.read(1024)
                if not chunk:
                    break
                chunked_buf.append(chunk)
                do_fp.write(chunk)
                md5_hash.update(chunk)
        hashes.update({fn: md5_hash.hexdigest()})

    update_manifest(session, collection_full_path, tmp_upload_path, hashes)
    merge_to_resource(session, tmp_upload_path, collection_full_path)
    response = 'Wrote files, updated manifest, and merged into resource\n'
    response += repr(hashes)
    return flask.Response(response)
upload_files.provide_automatic_options = False
upload_files.methods = ['POST']
