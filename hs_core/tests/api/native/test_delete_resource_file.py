

import unittest
import os

from django.contrib.auth.models import Group, User

from hs_core import hydroshare
from hs_core.models import ResourceFile, BaseResource
from hs_core.testing import MockIRODSTestCaseMixin


class TestDeleteResourceFile(MockIRODSTestCaseMixin, unittest.TestCase):
    def setUp(self):
        super(TestDeleteResourceFile, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'jamy2@gmail.com',
            username='jamy2',
            first_name='Tian',
            last_name='Gan',
            superuser=False,
            groups=[]
        )

        self.res = hydroshare.create_resource(resource_type='CompositeResource',
                                              owner=self.user,
                                              title='Test Resource',
                                              metadata=[],)

        test_file = open('myfile.txt', "w")
        test_file.write("Test text file in test1.txt")
        test_file.close()
        self.file = open('myfile.txt', 'rb')

        hydroshare.add_resource_files(self.res.short_id, self.file)

    def tearDown(self):
        super(TestDeleteResourceFile, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        self.res.delete()
        BaseResource.objects.all().delete()
        self.file.close()
        os.remove(self.file.name)

    def test_delete_file(self):
        # test if the test file is added to the resource
        resource_file_objects = ResourceFile.objects.filter(object_id=self.res.pk)
        self.assertIn(
            self.file.name,
            [os.path.basename(rf.resource_file.name) for rf in resource_file_objects],
            msg='the test file is not added to the resource'
        )
        self.assertEqual(27, self.res.size)

        # delete the resource file - this is the api we are testing
        hydroshare.delete_resource_file(self.res.short_id, self.file.name, self.user)
        # test if the added test file is deleted
        resource_file_objects = ResourceFile.objects.filter(object_id=self.res.pk)
        self.assertNotIn(
            self.file.name,
            [os.path.basename(rf.resource_file.name) for rf in resource_file_objects],
            msg='the added test file is not deleted from the resource'
        )
        self.assertEqual(0, self.res.size)
