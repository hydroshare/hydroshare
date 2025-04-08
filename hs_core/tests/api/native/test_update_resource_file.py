import os
import unittest

from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.testing import MockS3TestCaseMixin


class TestUpdateResourceFileAPI(MockS3TestCaseMixin, unittest.TestCase):
    def setUp(self):
        super(TestUpdateResourceFileAPI, self).setUp()
        self.hydroshare_author_group, _ = Group.objects.get_or_create(name='Hydroshare Author')

    def tearDown(self):
        super(TestUpdateResourceFileAPI, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        self.new_res.delete()
        BaseResource.objects.all().delete()
        self.original_file.close()
        os.remove(self.original_file.name)
        self.new_file.close()
        os.remove(self.new_file.name)

    def test_update_resource_file(self):
        # create a user to be used for creating the resource
        self.user_creator = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        self.new_res = hydroshare.create_resource(
            'CompositeResource',
            self.user_creator,
            'My Test Resource'
        )

        # resource should not have any files at this point
        self.assertEqual(self.new_res.files.all().count(), 0, msg="resource file count didn't match")

        # create a file
        original_file_name = 'original.txt'

        self.original_file = open(original_file_name, 'w')
        self.original_file.write("original text")
        self.original_file.close()

        original_file = open(original_file_name, 'rb')
        # add the file to the resource
        added_files = hydroshare.add_resource_files(self.new_res.short_id, original_file)

        # resource should have only one file at this point
        self.assertEqual(len(added_files), 1)
        self.assertEqual(self.new_res.files.all().count(), 1, msg="resource file count didn't match")

        self.assertIn(
            original_file_name,
            [os.path.basename(f.resource_file.name) for f in self.new_res.files.all()],
            msg='%s is not one of the resource files.' % original_file_name
        )

        # create a file that will be used to update the original file -1st update
        new_file_name = 'update.txt'    # file has a different name from the file that we will be updating
        self.new_file = open(new_file_name, 'w')
        new_file_data = 'data in new file'
        self.new_file.write(new_file_data)
        self.new_file.close()
        new_file = open(new_file_name, 'rb')

        # this is the api call we are testing
        rf = hydroshare.update_resource_file(self.new_res.short_id, original_file_name, new_file)

        # test if the file name matches
        self.assertEqual(os.path.basename(rf.resource_file.name), new_file_name, msg="resource file name didn't match")

        # since we are updating a file the number of files in the resource needs to be still 1
        self.assertEqual(self.new_res.files.all().count(), 1, msg="resource file count didn't match")

        # test if the content of the file matches
        resource_file = hydroshare.get_resource_file(self.new_res.short_id, new_file_name).resource_file
        self.assertEqual(resource_file.read().decode('utf-8'), new_file_data, msg="resource file content didn't match")

        # reset the original resource file name for 2nd time resource file update
        original_file_name = new_file_name

        # create a file that will be used to update the resource file - 2nd update
        new_file_name = 'update.txt'    # file has the same name as the file that we will be updating
        new_file = open(new_file_name, 'w')
        new_file_data = 'data in new file'
        new_file.write(new_file_data)
        new_file.close()
        new_file = open(new_file_name, 'rb')

        # this is the api call we are testing
        rf = hydroshare.update_resource_file(self.new_res.short_id, original_file_name, new_file)

        # test if the file name matches
        self.assertEqual(os.path.basename(rf.resource_file.name), new_file_name,
                         msg="{0} != {1}".format(os.path.basename(rf.resource_file.name), new_file_name))

        # exception ObjectDoesNotExist should be raised if resource does not have a file
        # for the given file name (file_not_in_resource.txt) to update
        with self.assertRaises(ObjectDoesNotExist):
            hydroshare.update_resource_file(self.new_res.short_id, 'file_not_in_resource.txt', new_file)
