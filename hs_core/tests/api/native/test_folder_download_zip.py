import os
import tempfile

from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core import hydroshare
from hs_core.hydroshare import resource
from hs_core.models import GenericResource
from hs_core.tasks import create_temp_zip


class TestFolderDownloadZip(TestCase):
    def setUp(self):
        super(TestFolderDownloadZip, self).setUp()
        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username='mytestuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group]
        )

        self.tmp_dir = tempfile.mkdtemp()

        # Make a text file
        self.txt_file_name = 'text.txt'
        self.txt_file_path = os.path.join(self.tmp_dir, self.txt_file_name)
        txt = open(self.txt_file_path, 'w')
        txt.write("Hello World\n")
        txt.close()

        self.raster_file_name = 'cea.tif'
        self.raster_file_path = 'hs_core/tests/data/cea.tif'

        self.rtype = 'GenericResource'
        self.title = 'My Test resource'
        self.test_res = resource.create_resource(self.rtype,
                                                 self.user,
                                                 self.title,
                                                 unpack_file=False)

        # create a folder 'foo'
        url = str.format('/hsapi/resource/{}/folders/foo/', self.test_res.short_id)
        self.client.put(url, {})

        # put a file 'test.txt' into folder 'foo'
        url2 = str.format('/hsapi/resource/{}/files/foo/', self.test_res.short_id)
        params = {'file': ('text.txt',
                           open(self.txt_file_path, 'rb'),
                           'text/plain')}
        self.client.post(url2, params)

        # put a file 'cea.tif' into folder 'foo'
        url3 = str.format('/hsapi/resource/{}/files/foo/', self.test_res.short_id)
        params = {'file': (self.raster_file_name,
                           open(self.raster_file_path, 'rb'),
                           'image/tiff')}
        self.client.post(url3, params)

    def tearDown(self):
        super(TestFolderDownloadZip, self).tearDown()
        if self.test_res:
            self.test_res.delete()
        GenericResource.objects.all().delete()

    def test_create_temp_zip(self):
        try:
            create_temp_zip(self.test_res.short_id, "/data/contents/foo", "zips/rand/foo.zip")
        except Exception as ex:
            self.fail("create_temp_zip() raised exception.{}".format(ex.message))
