# test file for delete_resource_file   Tian Gan
from __future__ import absolute_import
import os
from unittest import TestCase
from hs_core import hydroshare
from hs_core.models import ResourceFile, GenericResource
from django.contrib.auth.models import User

class TestDeleteResourceFile(TestCase):
    def setUp(self):
        self.user = hydroshare.create_account(
            'jamy2@gmail.com',
            username='jamy2',
            first_name='Tian',
            last_name='Gan',
            superuser=False,
            groups=[]
        )

        self.res = GenericResource.objects.create(
            user=self.user,
            title='My resource',
            creator=self.user,
            last_changed_by=self.user,
        )

        self.file = open('myfile.txt', "w")
        self.file = open('myfile.txt','r')

        hydroshare.add_resource_files(self.res.short_id, self.file)

    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()
        ResourceFile.objects.all().delete()

    def test_delete_file(self):
        # test if the test file is added to the resource
        resource_file_objects = ResourceFile.objects.filter(object_id=self.res.pk)
        self.assertIn(
            self.file.name,
            [os.path.basename(rf.resource_file.name) for rf in resource_file_objects],
            msg='the test file is not added to the resource'
        )


        # test if the added test file is deleted
        hydroshare.delete_resource_file(self.res.short_id, self.file.name)
        resource_file_objects = ResourceFile.objects.filter(object_id=self.res.pk)
        self.assertNotIn(
            self.file.name,
            [os.path.basename(rf.resource_file.name) for rf in resource_file_objects],
            msg='the added test file is not deleted from the resource'
        )
