from irods_utils import irods_get, walk_get_data_objects, get_irods_session, join_paths

import flask

from zipstream import ZipperChunkedIOStream, ZIP_DEFLATED
import mimetypes

app = flask.Flask(__name__)


BUFFER_SIZE_MiB = .25
BUFFER_SIZE_BYTES = int(round((2**20) * BUFFER_SIZE_MiB))

def download_collection(short_key):
    app.logger.info('Starting download of {}'.format(short_key))
    collection = irods_get(short_key, 'collection')
    data_objects = walk_get_data_objects(collection)
    data_object_streams = [do.open() for do in data_objects]
    base_path = get_irods_session().base_path
    data_object_paths = [do.path[len(base_path):] for do in data_objects]

    zipstream = ZipperChunkedIOStream(compression=ZIP_DEFLATED)

    stream_generator = zipstream.chunked_add_file_streams(data_object_streams,
                                                          data_object_paths,
                                                          chunk_size=BUFFER_SIZE_BYTES)
    return flask.Response(stream_generator, mimetype='application/zip')


def download_file(data_object_path):
    data_object_path.strip('/')
    app.logger.info('Starting download of {}'.format(data_object_path))
    fp = irods_get(data_object_path, 'data_object').open('r')
    return flask.Response(fp, mimetype=mimetypes.guess_type(data_object_path)[0])
