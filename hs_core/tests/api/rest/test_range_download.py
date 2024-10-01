import os
import urllib.parse
import tempfile

from rest_framework import status

from hs_core.hydroshare import resource
from hs_core.models import RangedFileReader
from .base import HSRESTTestCase


class TestRangeDownload(HSRESTTestCase):
    def setUp(self):
        super(TestRangeDownload, self).setUp()

        self.tmp_dir = tempfile.mkdtemp()

        # Make a text file
        self.txt_file_name = 'text.txt'
        self.txt_file_path = os.path.join(self.tmp_dir, self.txt_file_name)
        txt = open(self.txt_file_path, 'w')
        txt.write("Hello World\n")
        txt.close()

        self.rtype = 'CompositeResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title,
                                       unpack_file=False)

        self.res = res
        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)

        # create a folder 'foo'
        url = str.format('/hsapi/resource/{}/folders/foo/', self.pid)
        self.client.put(url, {})

        # put a file 'test.txt' into folder 'foo'
        url2 = str.format('/hsapi/resource/{}/files/foo/', self.pid)
        params = {'file': ('text.txt',
                           open(self.txt_file_path, 'rb'),
                           'text/plain')}
        self.client.post(url2, params)

        self.prefix = f"/django_irods/rest_download/{self.pid}/data/contents/foo/"
        url = f"{self.prefix}{self.txt_file_name}/"
        params = {'url_download': False, 'zipped': False, 'aggregation': False}
        self.file_download_url = url + '?' + urllib.parse.urlencode(params)

    def test_accept_ranges(self):
        """
        Test case to verify if the server supports range requests.

        This test sends a GET request to the file download URL and checks if the 'Accept-Ranges' header is present.
        It also verifies that the value of the 'Accept-Ranges' header is set to 'bytes'.
        """
        response = self.client.get(self.file_download_url)
        self.assertIn('Accept-Ranges', response.headers)
        self.assertEqual(response.headers['Accept-Ranges'], 'bytes')

    def test_syntactically_invalid_ranges(self):
        """
        Test that a syntactically invalid byte range header is ignored and the
        response gives back the whole resource as per RFC 2616, section 14.35.1
        """
        content = open(self.txt_file_path).read()
        invalid = ["megabytes=1-2", "bytes=", "bytes=3-2", "bytes=--5", "units", "bytes=-,"]
        for range_ in invalid:
            response = self.client.get(self.file_download_url, HTTP_RANGE=range_)
            self.assertEqual(content, b''.join(response).decode('utf-8'))

    def test_unsatisfiable_range(self):
        """Test that an unsatisfiable range results in a 416 HTTP status code"""
        content = open(self.txt_file_path).read()
        # since byte ranges are *inclusive*, 0 to len(content) would be unsatisfiable
        response = self.client.get(self.file_download_url, HTTP_RANGE="bytes=0-%d" % len(content))
        self.assertEqual(response.status_code, 416)

    def test_ranges(self):
        # set the block size to something small so we do multiple iterations in
        # the RangedFileReader class
        original_block_size = RangedFileReader.block_size
        RangedFileReader.block_size = 3

        content = open(self.txt_file_path).read()
        # specify the range header, the expected response content, and the
        # values of the content-range header byte positions
        ranges = {
            "bytes=0-10": (content[0:11], (0, 10)),
            "bytes=2-3": (content[2:4], (2, 3)),
            "bytes=9-9": (content[9:10], (9, 9)),
            "bytes=-5": (content[len(content) - 5:], (len(content) - 5, len(content) - 1)),
            "bytes=3-": (content[3:], (3, len(content) - 1)),
            "bytes=-%d" % (len(content) + 1): (content, (0, len(content) - 1)),
        }
        for range_, (expected_result, byte_positions) in ranges.items():
            response = self.client.get(self.file_download_url, HTTP_RANGE=range_)
            self.assertEqual(expected_result, b''.join(response).decode('utf-8'))
            self.assertEqual(int(response['Content-Length']), len(expected_result))
            self.assertEqual(response['Content-Range'], "bytes %d-%d/%d" % (byte_positions + (len(content),)))

        RangedFileReader.block_size = original_block_size

    def test_resumable_download(self):
        """
        Test case for checking that downloads are resumable using the Range header.
        """

        # start a download and pause it partway through
        response = self.client.get(self.file_download_url, HTTP_RANGE='bytes=0-5')
        self.assertEqual(response.status_code, status.HTTP_206_PARTIAL_CONTENT)
        self.assertEqual(response['Content-Length'], '6')
        self.assertEqual(response['Content-Range'], 'bytes 0-5/12')
        self.assertEqual(b''.join(response), b'Hello ')

        # resume the download
        response = self.client.get(self.file_download_url, HTTP_RANGE='bytes=6-')
        self.assertEqual(response.status_code, status.HTTP_206_PARTIAL_CONTENT)
        self.assertEqual(response['Content-Length'], '6')
        self.assertEqual(response['Content-Range'], 'bytes 6-11/12')
        self.assertEqual(b''.join(response), b'World\n')

        # download the file in one go
        response = self.client.get(self.file_download_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Length'], '12')
        self.assertEqual(b''.join(response), b'Hello World\n')
