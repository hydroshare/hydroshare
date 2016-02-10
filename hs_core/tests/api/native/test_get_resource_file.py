from __future__ import absolute_import
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
            'jamy2@gmail.com',
            username='jamy2',
            first_name='Tian',
            last_name='Gan',
            superuser=False,
            groups=[]
        )

        self.res = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My resource',
            metadata=[],
        )

        open('myfile.txt', "w").close()
        self.file = open('myfile.txt', 'r')

        hydroshare.add_resource_files(self.res.short_id, self.file)

    def tearDown(self):
        super(TestGetResourceFile, self).tearDown()
        User.objects.all().delete()
        GenericResource.objects.all().delete()
        ResourceFile.objects.all().delete()
        self.file.close()
        os.remove(self.file.name)

    def test_get_file(self):
        # test if the added test file is obtained
        res_file_object = hydroshare.get_resource_file(self.res.short_id, self.file.name)
        self.assertEqual(
            self.file.name,
            os.path.basename(res_file_object.name),
            msg='file name did not match'
        )
