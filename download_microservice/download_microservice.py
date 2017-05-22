#!/usr/bin/env python

import gevent.monkey
import gevent.pywsgi
from gevent.queue import PriorityQueue, Queue, Empty
from gevent.pool import Group
from gevent import socket

gevent.monkey.patch_all()

from dotenv import load_dotenv
from irods.session import iRODSSession
from irods.exception import CollectionDoesNotExist, DataObjectDoesNotExist

import logging
import random
import os
import sys
import flask
import stat
from flask import g

app = flask.Flask(__name__)

level = logging.ERROR
log_file_handler = logging.FileHandler('download_microservice.log')
for module in [__name__, 'werkzeug', 'irods.pool']:
    log = logging.getLogger(module)
    log.setLevel(level)
    log.addHandler(log_file_handler)
    log.addHandler(logging.StreamHandler(sys.stdout))

BUFFER_SIZE_MiB = 1.75
BUFFER_SIZE_BYTES = int(round((2**20) * BUFFER_SIZE_MiB))
RETRY_THRESHOLD = 5

def get_irods_session():
    irods_session = getattr(g, '_irods_session', None)
    if irods_session is None:
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(dotenv_path)
        host = os.getenv('IRODS_HOST', None)
        port = int(os.getenv('IRODS_PORT', None))
        user = os.getenv('IRODS_USER', None)
        zone = os.getenv('IRODS_ZONE', None)
        password = os.getenv('IRODS_PASSWORD', None)
        threads = int(os.getenv('IRODS_THREADS', 0))
        base_path = os.getenv('IRODS_BASE_PATH')
        irods_session = g._irods_session = iRODSSession(host=host, port=port, user=user, zone=zone, password=password, numThreads=threads)
        irods_session.base_path = base_path
    return irods_session

@app.teardown_appcontext
def teardown_session(exception):
    irods_session = getattr(g, '_irods_session', None)
    if irods_session is not None:
        del irods_session

class irodsReader(gevent.Greenlet):
    # Stores a greenlet id (grid), allocated buffer, and connection (data obj)
    def __init__(self, grid, do, buf_size, work, out_queue):
        super(irodsReader, self).__init__()
        self.do = do
        self.grid = grid
        self.work = work
        self.buffer = bytearray(buf_size)
        self.out_queue = out_queue

    def __str__(self):
        return 'Reader: {}'.format(self.grid)

    def _run(self):
        gevent.sleep(random.randint(0,2)*0.001)
        stream = self.do.open('r')
        while not self.work.empty():
            network_error = False
            gevent.sleep(random.randint(0,2)*0.001)
            work_id, start_pos = self.work.get()
            app.logger.debug("Begin read {} work_id:{} pos:{}".format(self, work_id, start_pos))
            try:
               stream.seek(start_pos)
               read_s = stream.readinto(self.buffer)
               gevent.sleep(random.randint(0,2)*0.001)
            except:
               app.logger.info("Seek or read fail {} wid: {}".format(self, work_id))
               self.work.put((work_id, start_pos))
               network_error = True
            else:
               self.out_queue.put((work_id, self.buffer[:read_s]))
            if network_error:
                with app.app_context():
                    app.read_failure_count += 1
                    stream = self.do.open('r')
                    if app.read_failure_count > RETRY_THRESHOLD:
                        app.read_failure_count = 0
                        # add more handling here
                        raise Exception('Network retry threshold met')
                gevent.sleep(random.randint(0,5)*0.001)
        app.logger.info("{} finished work".format(self))

# Order and group results into chunks on a queue.
def chunker(write_queue, chunk_queue, total_units):
    next_work_id = 0
    app.logger.debug('Starting to group chunks')
    while next_work_id < total_units:
        app.logger.debug('Chunk grouper: {}/{} wq:{}'.format(next_work_id, total_units, len(chunk_queue)))
        pending_sequential_data = bytearray()
        while len(chunk_queue) > 0 and chunk_queue.peek()[0] == next_work_id and next_work_id < total_units:
            work_id, data = chunk_queue.get()
            pending_sequential_data.extend(data)
            next_work_id += 1
        # May be an empty byte array indicating that nothing has been added
        write_queue.put(pending_sequential_data)
        gevent.sleep(random.randint(0,5)*.001)
    # None signals the writer that we have no more messages
    write_queue.put(None)
    app.logger.info("Finished grouping chunks")

# Yield chunks for the chunk queue as a generator
def chunk_generator(write_queue, readers_group, chunker_worker):
    app.logger.info('Starting to generate chunks')
    while 1:
        try:
            chunk = write_queue.get_nowait()
            if chunk is not None:
                app.logger.debug('Yielding chunk')
                try:
                    yield chunk
                except GeneratorExit:
                    readers_group.kill()
                    chunker_worker.kill()
                    app.logger.info('Chunk generator early exit')
                    raise GeneratorExit
            else:
                app.logger.info('Chunker finished, breaking loop')
                break
        except Empty:
            app.logger.debug('Chunk queue is empty')
            yield ''
        gevent.sleep(random.randint(0,5)*.001)
    app.logger.info('Chunk generator is finished')
    readers_group.kill()
    chunker_worker.kill()
 
def open_data_object(path):
    session = get_irods_session()
    data_object_path = session.base_path + path
    try:
        data_object = session.data_objects.get(data_object_path)
    except (CollectionDoesNotExist, DataObjectDoesNotExist):
        app.logger.error('404: Could not find {}'.format(data_object_path))
        flask.abort(404)
    return data_object

@app.route('/download/<path:data_object_path>')
def download(data_object_path):
    app.read_failure_count = 0

    data_object = open_data_object(data_object_path)

    app.logger.info('Starting download of {} ({} bytes)'.format(data_object_path, data_object.size))
    def define_work(full_size, chunk_size):
        work = PriorityQueue()
        for work_id, start_pos in enumerate(range(0, full_size, chunk_size)):
            work.put((work_id, start_pos))
        return work
    tasks = define_work(data_object.size, BUFFER_SIZE_BYTES)

    chunk_queue = PriorityQueue()
    write_queue = Queue()
    readers_group = Group()
    for grid in range(get_irods_session().numThreads):
        readers_group.start(irodsReader(grid, data_object, BUFFER_SIZE_BYTES, tasks, chunk_queue))
    chunker_worker = gevent.spawn(chunker, write_queue, chunk_queue, len(tasks))

    return flask.Response(chunk_generator(write_queue, readers_group, chunker_worker), mimetype='image/jpeg')

if __name__ == '__main__':
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) 
    sock_path = '/hs_download_microservice/' + os.path.basename(__file__) + '.sock'


    logging.info('Creating unix file socket')
    if os.path.exists(sock_path):
        os.remove(sock_path)
    logging.info('Binding to sock file.')
    listener.bind(sock_path)
    os.chmod(sock_path, stat.S_IROTH |  stat.S_IWOTH)
    listener.listen(1)
    gevent.pywsgi.WSGIServer(listener, app).serve_forever()

    # TODO get secondary listener working for debugging
    #logging.info('Listening on tcp port 5000')
    #gevent_server = gevent.pywsgi.WSGIServer(('', 5000), app)
    #gevent_server.serve_forever()

