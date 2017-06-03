#!/usr/bin/env python3

from collections import deque
from zipfile import ZIP_STORED, ZIP_LZMA, ZIP_DEFLATED, ZIP_BZIP2
from zipfile import ZipFile, ZipInfo
import os

__all__ = ['ZipperChunkedIOStream', 'ZIP_STORED', 'ZIP_LZMA', 'ZIP_DEFLATED', 'ZIP_BZIP2']


class ChunkedBuffer:
    """
    This is a pseudo-buffer that stores pre-chunked data in a queue.  It is
    used to store results of zip operations on chunked reads and maintain
    chunked output.
    """

    def __init__(self):
        self.chunks = deque()

    def read(self):
        return self.chunks.popleft()

    def write(self, o):
        self.chunks.append(o)
        return len(o)

    def flush(self):
        pass

    def __iter__(self):
        return self

    def __next__(self):
        if self:
            return self.read()
        else:
            raise StopIteration

    def __bool__(self):
        return bool(self.chunks)


class ZipperChunkedIOStream:
    """
    Uses a queue to store read chunks from either local file paths or RawIOBase
    derived buffers. These will either be zipped and yielded as read in via a
    generator.
    """

    def __init__(self, compression=ZIP_STORED):
        self.zip_file_stream = ChunkedBuffer()
        self.zip_file = ZipFile(file=self.zip_file_stream, mode='w', compression=compression,
                                allowZip64=True)

    def chunked_add_file_paths(self, file_paths, chunk_size):
        file_streams = [open(path, 'rb') for path in file_paths]
        yield from self.chunked_add_file_streams(file_streams, file_paths, chunk_size)  # NOQA

    def chunked_add_file_streams(self, streams, stream_filenames, chunk_size):
        # yield a blank string so that hopefully nothing blocks too long here.
        yield b''
        for in_stream, in_file_name in zip(streams, stream_filenames):
            zinfo = ZipInfo(in_file_name)
            # since the ZipFile is not creating the ZipInfo, we need to set
            #  the compression level manually.
            zinfo.compress_type = self.zip_file.compression
            out_stream = self.zip_file.open(zinfo, 'w')

            eof = False
            while not eof:
                chunk = in_stream.read(chunk_size)
                out_stream.write(chunk)
                yield from self.zip_file_stream  # NOQA
                if not chunk:
                    eof = True
            out_stream.close()
            yield from self.zip_file_stream  # NOQA
        self.zip_file.close()
        yield from self.zip_file_stream  # NOQA


if __name__ == '__main__':
    """
    Run this file individually to test output.
    """
    def finalized_write():
        """
        Wait until all of the chunks have been created to convert them to a
        list and write them all out to disk.
        """
        zstream = ZipperChunkedIOStream(compression=ZIP_DEFLATED)
        local_file_paths = ['zipstream.py', 'download_microservice.py']
        chunks = list(zstream.chunked_add_file_paths(local_file_paths, chunk_size=1024))

        with open('out_finalized.zip', 'wb') as out_finalized_fp:
            for chunk in chunks:
                out_finalized_fp.write(chunk)
            out_finalized_fp.close()

    def subdirectories():
        """
        Create a zip with subdirectories
        """
        os.chdir('..')
        zstream = ZipperChunkedIOStream(compression=ZIP_DEFLATED)
        local_file_paths = ['download_microservice/zipstream.py', 'download_microservice/download_microservice.py']
        chunks = list(zstream.chunked_add_file_paths(local_file_paths, chunk_size=1024))

        with open('download_microservice/subdirectories.zip', 'wb') as out_finalized_fp:
            for chunk in chunks:
                out_finalized_fp.write(chunk)
            out_finalized_fp.close()
        os.chdir('download_microservice')

    def streaming_write():
        """
        Write the zipfile immediately as zipfile chunks are yielded.
        """
        zs = ZipperChunkedIOStream(compression=ZIP_DEFLATED)
        with open('out_streaming.zip', 'wb') as out_streaming_fp:
            local_file_paths = ['zipstream.py', 'download_microservice.py']
            for chunk in zs.chunked_add_file_paths(local_file_paths, chunk_size=1024):
                out_streaming_fp.write(chunk)
            out_streaming_fp.close()

    finalized_write()
    subdirectories()
    streaming_write()
