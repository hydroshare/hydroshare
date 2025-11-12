import os
import urllib.parse
import tempfile

from rest_framework import status

from hs_core.hydroshare import resource
from .base import HSRESTTestCase


class TestBagitDownload(HSRESTTestCase):
    def setUp(self):
        super(TestBagitDownload, self).setUp()

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

    def test_bag_last_downloaded_date(self):
        """
        Test case for checking the last downloaded date of a bag.
        """
        res = self.res

        last_downloaded_date = res.bag_last_downloaded
        self.assertIsNone(last_downloaded_date)

        self.assertEqual(res.download_count, 0)

        zip_download_url = f"/django_s3/rest_download/bags/{res.short_id}.zip?"
        params = {'url_download': False, 'zipped': False, 'aggregation': False}
        zip_download_url += urllib.parse.urlencode(params)

        # download the bag for the first time
        response = self.client.get(zip_download_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        res.refresh_from_db()
        pre_last_downloaded_date = res.bag_last_downloaded
        self.assertIsNotNone(pre_last_downloaded_date)

        self.assertEqual(res.download_count, 1)

        # download again
        response = self.client.get(zip_download_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        res.refresh_from_db()
        post_last_downloaded_date = res.bag_last_downloaded

        self.assertGreater(post_last_downloaded_date, pre_last_downloaded_date)

        self.assertEqual(res.download_count, 2)
