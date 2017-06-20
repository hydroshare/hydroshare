import io
import logging

import flask
from flask.wrappers import Request

from deposit import upload_files
from download import download_collection, download_file


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

app.add_url_rule('/upload_files/<string:short_key>/data/',
                 view_func=upload_files)
app.add_url_rule('/download_collection/<string:short_key>.zip/',
                 view_func=download_collection)
app.add_url_rule('/download/<path:data_object_path>/',
                 view_func=download_file)

if __name__ == '__main__':
    app.logger.setLevel(logging.DEBUG)
    with app.app_context():
        app.run(host='0.0.0.0', port=5000, debug=True)
