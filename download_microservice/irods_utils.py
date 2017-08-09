import os
from dotenv import load_dotenv
from flask import g
import flask
from irods.exception import CollectionDoesNotExist, DataObjectDoesNotExist
from irods.session import iRODSSession

app = flask.Flask(__name__)


def join_paths(p1, p2):
    """
    Like os.join(), but for iRODS.
    """
    if p1.endswith('/'):
        p1 = p1[:-1]
    if p2.startswith('/'):
        p2 = p2[1:]
    return p1 + '/' + p2


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
