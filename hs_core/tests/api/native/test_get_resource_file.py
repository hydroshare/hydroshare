
import os
from unittest import TestCase

from django.contrib.auth.models import Group

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin


class TestGetResourceFile(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestGetResourceFile, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'get_resource_file_test_user@gmail.com',
            username='get_res_file_test_user',
            first_name='test',
            last_name='user',
            superuser=False
        )

        self.res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test File'
        )

        test_file = open('test1.txt', 'w')
        test_file.write("Test text file in test1.txt")
        test_file.close()
        self.file = open('test1.txt', 'rb')
        hydroshare.add_resource_files(self.res.short_id, self.file)

    def tearDown(self):
        super(TestGetResourceFile, self).tearDown()
        self.file.close()
        os.remove(self.file.name)

    def test_get_file(self):
        # test if the added test file is obtained
        res_file = hydroshare.get_resource_file(self.res.short_id,
                                                self.file.name)
        res_file_object = res_file.resource_file
        self.assertEqual(
            self.file.name,
            os.path.basename(res_file_object.name),
            msg='file name did not match'
        )

        # test if the last modified time for the file can be obtained
        # assert time is not None without iRODS Session Exception being raised
        self.assertTrue(res_file.modified_time)
        self.assertTrue(res_file.checksum)
