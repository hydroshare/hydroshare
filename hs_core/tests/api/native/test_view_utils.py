import os

from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.test import TestCase

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.views.utils import create_folder, move_to_folder, list_folder, rename_file_or_folder

class TestViewUtils(MockIRODSTestCaseMixin, TestCase):
    def test_move_to_folder_basic(self):
        group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        resource = hydroshare.create_resource(
            'GenericResource',
            user,
            'test resource',
        )

        resource.doi = 'doi1000100010001'
        resource.save()

        open('myfile.txt', "w").close()
        file = open('myfile.txt', 'r')

        hydroshare.add_resource_files(resource.short_id, file)
        create_folder(resource.short_id, "data/contents/test_folder")

        move_to_folder(user, resource.short_id,
                       src_paths=['data/contents/myfile.txt'],
                       tgt_path="data/contents/test_folder",
                       validate_move_rename=True)

        folder_contents = list_folder(resource.short_id, "data/contents/test_folder")
        self.assertEquals(True, ['myfile.txt'] in folder_contents)

        resource.delete()
        group.delete()
        user.delete()

    def test_rename_file_or_folder(self):
        group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        resource = hydroshare.create_resource(
            'GenericResource',
            user,
            'test resource',
        )

        resource.doi = 'doi1000100010001'
        resource.save()

        open('myfile.txt', "w").close()
        file = open('myfile.txt', 'r')

        hydroshare.add_resource_files(resource.short_id, file)
        create_folder(resource.short_id, "data/contents/test_folder")

        rename_file_or_folder(user, resource.short_id,
                              src_path="data/contents/myfile.txt",
                              tgt_path="data/contents/myfile2.txt",
                              validate_move_rename=True)

        rename_file_or_folder(user, resource.short_id,
                              src_path="data/contents/test_folder",
                              tgt_path="data/contents/test_folder2",
                              validate_move_rename=True)

        folder_contents = list_folder(resource.short_id, "data/contents/")
        self.assertEquals(True, ['myfile2.txt'] in folder_contents)
        self.assertEquals(True, ['test_folder2'] in folder_contents)

        resource.delete()
        group.delete()
        user.delete()

    def test_irods_path_is_directory(self):
        pass