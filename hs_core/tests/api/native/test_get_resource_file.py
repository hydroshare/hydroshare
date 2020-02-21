
import os
from unittest import TestCase

from django.contrib.auth.models import User, Group

from hs_core import hydroshare
from hs_core.models import ResourceFile, GenericResource
from hs_core.testing import MockIRODSTestCaseMixin


class TestGetResourceFile(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestGetResourceFile, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'testuser@gmail.com',
            username='testuser',
            first_name='test',
            last_name='user',
            superuser=False,
            groups=[]
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
        res_file_object = hydroshare.get_resource_file(self.res.short_id,
                                                       self.file.name).resource_file
        self.assertEqual(
            self.file.name,
            os.path.basename(res_file_object.name),
            msg='file name did not match'
        )

        # test if the last modified time for the file can be obtained
        istorage = self.res.get_irods_storage()
        time = istorage.get_modified_time(res_file_object.name)
        # assert time is not None without iRODS Session Exception being raised
        self.assertTrue(time)
