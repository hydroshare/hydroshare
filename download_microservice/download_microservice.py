#!/usr/bin/env python

import logging
import os
import mimetypes

from dotenv import load_dotenv
import flask
from flask import g
from irods.session import iRODSSession
from irods.exception import CollectionDoesNotExist, DataObjectDoesNotExist

from zipstream import ZipperChunkedIOStream, ZIP_DEFLATED

app = flask.Flask(__name__)
BUFFER_SIZE_MiB = .25
BUFFER_SIZE_BYTES = int(round((2**20) * BUFFER_SIZE_MiB))
RETRY_THRESHOLD = 5


def get_irods_session():
    irods_session = getattr(g, '_session', None)
    if irods_session is None:
        app.logger.debug('Getting session')
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(dotenv_path)
        session_kwargs = {
            'host': os.getenv('IRODS_HOST', None),
            'port': int(os.getenv('IRODS_PORT', None)),
            'user': os.getenv('IRODS_USER', None),
            'zone': os.getenv('IRODS_ZONE', None),
            'password': os.getenv('IRODS_PASSWORD', None),
            'numThreads': int(os.getenv('IRODS_THREADS', 0)),
        }
        g._session = irods_session = iRODSSession(**session_kwargs)
        irods_session.base_path = os.getenv('IRODS_BASE_PATH')
    return irods_session


def irods_get(path, irods_type):
    app.logger.debug('Locating iRODS item')
    session = get_irods_session()
    irods_path = session.base_path + path
    try:
        if irods_type == 'data object':
            irods_item = session.data_objects.get(irods_path)
        elif irods_type == 'collection':
            irods_item = session.collections.get(irods_path)
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
    # TODO: retain directory structure in resultant zip file.
    data_object_filenames = [do.path.split('/')[-1] for do in data_objects]

    zipstream = ZipperChunkedIOStream(compression=ZIP_DEFLATED)

    stream_generator = zipstream.chunked_add_file_streams(data_object_streams,
                                                          data_object_filenames,
                                                          chunk_size=BUFFER_SIZE_BYTES)
    return flask.Response(stream_generator, mimetype='application/zip')


@app.route('/download/<path:data_object_path>/')
@app.route('/download/<path:data_object_path>')
def download(data_object_path):
    app.logger.info('Starting download of {}'.format(data_object_path))
    fp = irods_get(data_object_path, 'data object').open('r')
    return flask.Response(fp, mimetype=mimetypes.guess_type(data_object_path)[0])


if __name__ == '__main__':
    level = logging.DEBUG
    app.logger.setLevel(logging.DEBUG)
    with app.app_context():
        app.run(host='0.0.0.0', port=5000)
