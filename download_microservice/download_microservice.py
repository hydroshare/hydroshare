#!/usr/bin/env python

import logging
import os
import mimetypes
import io
from collections import deque
import hashlib

from dotenv import load_dotenv
import flask
from flask import g
from flask.wrappers import Request
from irods.session import iRODSSession
from irods.exception import CollectionDoesNotExist, DataObjectDoesNotExist

from zipstream import ZipperChunkedIOStream, ZIP_DEFLATED


def file_stream_factory(total_content_length, filename, content_type,
                        content_length=None):
    return io.BytesIO()


class StreamingFilesRequest(Request):
    def _get_file_stream(self, total_content_length, content_type,
                         filename=None, content_length=None):
        return file_stream_factory(total_content_length, content_type,
                                   filename, content_length)

app = flask.Flask(__name__)
app.request_class = StreamingFilesRequest

BUFFER_SIZE_MiB = .25

BUFFER_SIZE_BYTES = int(round((2**20) * BUFFER_SIZE_MiB))
RETRY_THRESHOLD = 5


def get_irods_session():
    irods_session = getattr(g, '_session', None)
    if irods_session is None:
        app.logger.debug('Getting session')
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(dotenv_path)
        variables = ['IRODS_HOST', 'IRODS_PORT', 'IRODS_ZONE', 'IRODS_USER',
                     'IRODS_PASSWORD']
        if not all([var in os.environ for var in variables]):
            app.logger.error('Not enough information available to establish '
                             'iRODS connection. Be sure to set env variables.')
            exit(-1)
        session_kwargs = {
            'host': os.getenv('IRODS_HOST'),
            'port': int(os.getenv('IRODS_PORT')),
            'zone': os.getenv('IRODS_ZONE'),
            'user': os.getenv('IRODS_USER'),
            'password': os.getenv('IRODS_PASSWORD'),
            'numThreads': int(os.getenv('IRODS_THREADS', 0)),
        }
        g._session = irods_session = iRODSSession(**session_kwargs)
        irods_session.base_path = os.getenv('IRODS_BASE_PATH')
        irods_session.upload_path = os.getenv('IRODS_UPLOAD_PATH')
    return irods_session


def irods_get(path, irods_type):
    app.logger.debug('Locating iRODS item')
    session = get_irods_session()
    irods_path = session.base_path + path
    try:
        if irods_type == 'data_object':
            irods_item = session.data_objects.get(irods_path)
        elif irods_type == 'collection':
            irods_item = session.collections.get(irods_path)
        else:
            raise ValueError('Unknown irods_type. Cannot get item.')
    except (CollectionDoesNotExist, DataObjectDoesNotExist):
        app.logger.error('404: Could not find {}'.format(irods_path))
        flask.abort(404)
    app.logger.debug('iRODS item found')
    return irods_item


def walk_get_data_objects(root_collection):
    data_objects = []
    subcollections = [root_collection]
    while subcollections:
        collection = subcollections.pop()
        if collection.data_objects:
            data_objects.extend(collection.data_objects)
        if collection.subcollections:
            subcollections.extend(collection.subcollections)
    return data_objects


@app.route('/download_collection/<path:collection_path>.zip/')
@app.route('/download_collection/<path:collection_path>.zip')
def download_collection(collection_path):
    app.logger.info('Starting download of {}'.format(collection_path))
    collection = irods_get(collection_path, 'collection')
    data_objects = walk_get_data_objects(collection)
    data_object_streams = [do.open() for do in data_objects]
    base_path = get_irods_session().base_path
    data_object_paths = [do.path[len(base_path):] for do in data_objects]

    zipstream = ZipperChunkedIOStream(compression=ZIP_DEFLATED)

    stream_generator = zipstream.chunked_add_file_streams(data_object_streams,
                                                          data_object_paths,
                                                          chunk_size=BUFFER_SIZE_BYTES)
    return flask.Response(stream_generator, mimetype='application/zip')


@app.route('/download/<path:data_object_path>/')
@app.route('/download/<path:data_object_path>')
def download(data_object_path):
    app.logger.info('Starting download of {}'.format(data_object_path))
    with irods_get(data_object_path, 'data_object').open('r') as fp:
        return flask.Response(fp, mimetype=mimetypes.guess_type(data_object_path)[0])


def write_manifest(session, col_base_path, filename_hashes):
    manifest_do = session.data_objects.create(col_base_path + 'manifest-md5.txt')
    with manifest_do.open('w') as do_fp:
        for md5, fn in filename_hashes:
            line = '{} {}\n'.format(md5, fn)
            do_fp.write(bytes(line, encoding='utf8'))


@app.route('/upload_files/<path:data_object_path>/', methods=['POST'])
@app.route('/upload_files/<path:data_object_path>', methods=['POST'])
def add_file(data_object_path):
    app.logger.info('Starting upload of {}'.format(data_object_path))
    session = get_irods_session()

    fake_short_key = hashlib.md5(os.urandom(1024)).hexdigest()
    collection_path = session.upload_path + fake_short_key
    session.collections.create(collection_path)
    collection_path = collection_path + '/'
    data_path = collection_path + 'data'
    session.collections.create(data_path)
    data_path = data_path + '/'

    hashes = []
    for fn in flask.request.files:
        md5_hash = hashlib.md5()
        stream = flask.request.files[fn].stream
        data_object = session.data_objects.create(data_path + fn)
        with data_object.open('w') as do_fp:
            chunked_buf = deque()
            while True:
                chunk = stream.read(10)
                if not chunk:
                    break
                chunked_buf.append(chunk)
                do_fp.write(chunk)
                md5_hash.update(chunk)
        hashes.append((fn, md5_hash.hexdigest()))

    write_manifest(session, collection_path, hashes)
    response = 'Wrote files and updated manifest\n'
    response += repr(hashes)
    return flask.Response(response)


if __name__ == '__main__':
    level = logging.DEBUG
    app.logger.setLevel(logging.DEBUG)
    with app.app_context():
        app.run(host='0.0.0.0', port=5000, debug=True)
