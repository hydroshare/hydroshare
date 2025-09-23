from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core.testing import MockS3TestCaseMixin
from hs_core import hydroshare
from hs_core.views.utils import create_folder, move_to_folder, list_folder, rename_file_or_folder


class TestViewUtils(MockS3TestCaseMixin, TestCase):
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
            'CompositeResource',
            user,
            'test resource',
        )

        resource.save()

        open('myfile.txt', "w").close()
        file = open('myfile.txt', 'rb')

        hydroshare.add_resource_files(resource.short_id, file)
        create_folder(resource.short_id, "data/contents/test_folder")

        move_to_folder(user, resource.short_id,
                       src_paths=['data/contents/myfile.txt'],
                       tgt_path="data/contents/test_folder",
                       validate_move=True)

        folder_contents = list_folder(resource.short_id, "data/contents/test_folder")
        self.assertTrue(['myfile.txt'] in folder_contents)

        resource.delete()

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
            'CompositeResource',
            user,
            'test resource',
        )

        resource.save()

        open('myfile.txt', "w").close()
        file = open('myfile.txt', 'rb')

        hydroshare.add_resource_files(resource.short_id, file)
        create_folder(resource.short_id, "data/contents/test_folder")

        rename_file_or_folder(user, resource.short_id,
                              src_path="data/contents/myfile.txt",
                              tgt_path="data/contents/myfile2.txt",
                              validate_rename=True)

        rename_file_or_folder(user, resource.short_id,
                              src_path="data/contents/test_folder",
                              tgt_path="data/contents/test_folder2",
                              validate_rename=True)

        folder_contents = list_folder(resource.short_id, "data/contents/")
        self.assertTrue(['myfile2.txt'] in folder_contents)
        self.assertTrue(['test_folder2'] in folder_contents)

        resource.delete()

    # TODO: test_s3_path_is_directory(self):
