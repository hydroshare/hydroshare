__author__ = 'Pabitra'

from django.test import TestCase
from django.contrib.auth.models import User
from hs_core import hydroshare
from hs_core.models import GenericResource, ResourceFile
from django.core.exceptions import ObjectDoesNotExist
import os
class TestUpdateResourceFileAPI(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()
        pass

    def test_update_resource_file(self):
        # create a user to be used for creating the resource
        user_creator = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        # create a resource without any owner
        resource = GenericResource.objects.create(
            user=user_creator,
            title='My resource',
            creator=user_creator,
            last_changed_by=user_creator,
            doi='doi1000100010001'
        )

        # resource should not have any files at this point
        self.assertEqual(resource.files.all().count(), 0, msg="resource file count didn't match")

        # create a file
        original_file_name = 'original.txt'

        original_file = open(original_file_name, 'w')
        original_file.write("original text")
        original_file.close()

        original_file = open(original_file_name, 'r')
        # add the file to the resource
        added_files = hydroshare.add_resource_files(resource.short_id, original_file)

        # resource should have only one file at this point
        self.assertEqual(len(added_files), 1)
        self.assertEqual(resource.files.all().count(), 1, msg="resource file count didn't match")

        self.assertIn(
            original_file_name,
            [os.path.basename(f.resource_file.name) for f in resource.files.all()],
            msg= '%s is not one of the resource files.' % original_file_name
        )

        # create a file that will be used to update the original file -1st update
        new_file_name = 'update.txt'    # file has a different name from the file that we will be updating
        new_file = open(new_file_name, 'w')
        new_file_data = 'data in new file'
        new_file.write(new_file_data)
        new_file.close()
        new_file = open(new_file_name, 'r')

        # this is the api call we are testing
        rf = hydroshare.update_resource_file(resource.short_id, original_file_name, new_file)

        # test if the file name matches
        self.assertEqual(os.path.basename(rf.resource_file.name), new_file_name, msg="resource file name didn't match")

        # since we are updating a file the number of files in the resource needs to be still 1
        self.assertEqual(resource.files.all().count(), 1, msg="resource file count didn't match")

        # test if the content of the file matches
        resource_file = hydroshare.get_resource_file(resource.short_id, new_file_name)
        self.assertEqual(resource_file.read(),  new_file_data, msg="resource file content didn't match")

        # reset the original resource file name for 2nd time resource file update
        original_file_name = new_file_name

        # create a file that will be used to update the resource file - 2nd update
        new_file_name = 'update.txt'    # file has the same name as the file that we will be updating
        new_file = open(new_file_name, 'w')
        new_file_data = 'data in new file'
        new_file.write(new_file_data)
        new_file.close()
        new_file = open(new_file_name, 'r')

        # this is the api call we are testing
        rf = hydroshare.update_resource_file(resource.short_id, original_file_name, new_file)

        # test if the file name matches
        self.assertEqual(os.path.basename(rf.resource_file.name), new_file_name,
                         msg="{0} != {1}".format(os.path.basename(rf.resource_file.name), new_file_name))

        # exception ObjectDoesNotExist should be raised if resource does not have a file
        # for the given file name (file_not_in_resource.txt) to update
        self.assertRaises(
            ObjectDoesNotExist,
            lambda: hydroshare.update_resource_file(resource.short_id, 'file_not_in_resource.txt', new_file)
        )

