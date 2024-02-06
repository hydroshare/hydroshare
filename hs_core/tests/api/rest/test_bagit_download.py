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

        self.raster_file_name = 'cea.tif'
        self.raster_file_path = 'hs_core/tests/data/cea.tif'

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

        last_downloaded_date = res.metadata.dates.filter(type='bag_last_downloaded').first()
        self.assertIsNone(last_downloaded_date)

        zip_download_url = f"/django_irods/rest_download/bags/{res.short_id}.zip?"
        params = {'url_download': False, 'zipped': False, 'aggregation': False}
        zip_download_url += urllib.parse.urlencode(params)

        # download the bag for the first time
        response = self.client.get(zip_download_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        pre_last_downloaded_date = res.metadata.dates.filter(type='bag_last_downloaded').first().start_date
        self.assertIsNotNone(pre_last_downloaded_date)

        # download again
        response = self.client.get(zip_download_url, format="json", follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        res.refresh_from_db()
        post_last_downloaded_date = res.metadata.dates.filter(type='bag_last_downloaded').first().start_date

        self.assertGreater(post_last_downloaded_date, pre_last_downloaded_date)
