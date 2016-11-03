import os
from unittest import TestCase

from django.conf import settings
from django.contrib.auth.models import Group, User

from django_irods.icommands import SessionException
from django_irods.storage import IrodsStorage

from hs_core.models import BaseResource
from hs_core.hydroshare import resource
from hs_core.hydroshare import utils
from hs_core import hydroshare
from hs_core.views.utils import run_ssh_command
from theme.models import UserProfile

class TestUserZoneIRODSFederation(TestCase):
    """
    This TestCase class tests all federation zone related functionalities, including creating
    resources in the federated user zone, adding files to resources in the user zone, creating
    a new version of a resource in the user zone, deleting resources in the user zone, and
    folder-related operations to the resource in the user zone
    """
    def setUp(self):
        super(TestUserZoneIRODSFederation, self).setUp()
        # only do federation testing when REMOTE_USE_IRODS is True and irods docker containers
        # are set up properly
        if not settings.REMOTE_USE_IRODS or settings.HS_USER_ZONE_HOST != 'users.local.org':
            return

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username='testuser',
            first_name='some_first_name',
            last_name='some_last_name',
            password = 'testuser',
            superuser=False,
            groups=[self.hs_group]
        )

        # create corresponding irods account in user zone
        try:
            exec_cmd = "{0} {1} {2}".format(settings.HS_USER_ZONE_PROXY_USER_CREATE_USER_CMD,
                                            'testuser', 'testuser')
            output = run_ssh_command(host=settings.HS_USER_ZONE_HOST,
                                     uname=settings.HS_USER_ZONE_PROXY_USER,
                                     pwd=settings.HS_USER_ZONE_PROXY_USER_PWD,
                                     exec_cmd=exec_cmd)
            if output:
                if 'ERROR:' in output.upper():
                    # irods account failed to create
                    self.assertRaises(SessionException(-1, output, output))

            user_profile = UserProfile.objects.filter(user=self.user).first()
            user_profile.create_irods_user_account = True
            user_profile.save()
        except Exception as ex:
            self.assertRaises(SessionException(-1, ex.message, ex.message))

        # create files
        self.file_one = "test1.txt"
        self.file_two = "test2.txt"
        self.file_to_be_deleted = "test_to_be_deleted.txt"

        test_file = open(self.file_one, 'w')
        test_file.write("Test text file in test1.txt")
        test_file.close()
        test_file = open(self.file_two, 'w')
        test_file.write("Test text file in test2.txt")
        test_file.close()
        test_file = open(self.file_to_be_deleted, 'w')
        test_file.write("Test text file which will be deleted after resource creation")
        test_file.close()

        # transfer files to user zone space
        self.irods_storage = IrodsStorage()
        self.irods_storage.set_user_session(username='testuser', password='testuser',
                                       host=settings.HS_USER_ZONE_HOST, port=settings.IRODS_PORT,
                                       zone=settings.HS_IRODS_LOCAL_ZONE_DEF_RES)
        self.irods_storage.saveFile(self.file_one, self.file_one)
        self.irods_storage.saveFile(self.file_two, self.file_one)
        self.irods_storage.saveFile(self.file_to_be_deleted, self.file_to_be_deleted)

        self.raster_file_path = 'hs_core/tests/data/cea.tif'
        # transfer cea.tif file to user zone space
        self.irods_storage.saveFile(self.raster_file_path, os.path.basename(self.raster_file_path))

    def tearDown(self):
        super(TestUserZoneIRODSFederation, self).tearDown()
        # no need for further cleanup if federation testing is not setup in the first place
        if not settings.REMOTE_USE_IRODS or settings.HS_USER_ZONE_HOST != 'users.local.org':
            return

        # delete irods test user in user zone
        try:
            exec_cmd = "{0} {1}".format(settings.HS_USER_ZONE_PROXY_USER_DELETE_USER_CMD,
                                        'testuser')
            output = run_ssh_command(host=settings.HS_USER_ZONE_HOST,
                                     uname=settings.HS_USER_ZONE_PROXY_USER,
                                     pwd=settings.HS_USER_ZONE_PROXY_USER_PWD,
                                     exec_cmd=exec_cmd)
            if output:
                if 'ERROR:' in output.upper():
                    # there is an error from icommand run, report the error
                    self.assertRaises(SessionException(-1, output, output))

            user_profile = UserProfile.objects.filter(user=self.user).first()
            user_profile.create_irods_user_account = False
            user_profile.save()
        except Exception as ex:
            # there is an error from icommand run, report the error
            self.assertRaises(SessionException(-1, ex.message, ex.message))

        self.user.uaccess.delete()
        self.user.delete()
        self.hs_group.delete()

        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()

        os.remove(self.file_one)
        os.remove(self.file_two)
        os.remove(self.file_to_be_deleted)

        # remove files from iRODS user zone as well
        # don't need to remove file_to_be_deleted from iRODS user zone since it will be removed
        # as part of tests
        self.irods_storage.delete(self.file_one)
        self.irods_storage.delete(self.file_two)
        self.irods_storage.delete(os.path.basename(self.raster_file_path))

    def test_resource_creation_and_deletion_in_user_zone(self):
        # test resource has one file
        fed_test_file_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_to_be_deleted)
        new_res = resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Test Generic Resource in User Zone',
            fed_res_file_names=[fed_test_file_full_path],
            fed_copy_or_move='move'
        )

        # test resource has one file
        self.assertEqual(new_res.files.all().count(), 1,
                         msg="Number of content files is not equal to 1")
        fed_path = '/{zone}/home/{user}'.format(zone=settings.HS_USER_IRODS_ZONE,
                                                user=settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
        self.assertEqual(new_res.resource_federation_path, fed_path)
        # test original file in user test zone is removed after resource creation
        # since 'move' is used for fed_copy_or_move when creating the resource
        self.assertFalse(self.irods_storage.exists(self.file_to_be_deleted))

        fed_test_file1_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_one)
        fed_test_file2_full_path = '/{zone}/home/testuser/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, fname=self.file_two)
        new_res = resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Test Generic Resource in User Zone',
            fed_res_file_names=[fed_test_file1_full_path, fed_test_file2_full_path],
            fed_copy_or_move='copy'
        )

        # test resource has two files
        self.assertEqual(new_res.files.all().count(), 2,
                         msg="Number of content files is not equal to 2")
        fed_path = '/{zone}/home/{user}'.format(zone=settings.HS_USER_IRODS_ZONE,
                                                user=settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
        self.assertEqual(new_res.resource_federation_path, fed_path)
        # test original two files in user test zone still exist after resource creation
        # since 'copy' is used for fed_copy_or_move when creating the resource
        self.assertTrue(self.irods_storage.exists(self.file_one))
        self.assertTrue(self.irods_storage.exists(self.file_two))

        # create a raster resource that represents a specific resource type
        fed_test_file_full_path = '/{zone}/home/testuser/cea.tif'.format(
            zone=settings.HS_USER_IRODS_ZONE)
        _, _, metadata, _ = utils.resource_pre_create_actions(
            resource_type='RasterResource',
            resource_title='Test Raster Resource',
            page_redirect_url_key=None,
            fed_res_file_names=[fed_test_file_full_path])
        new_res = resource.create_resource(
            resource_type='RasterResource',
            owner=self.user,
            title='My Test Raster Resource in User Zone',
            fed_res_file_names=[fed_test_file_full_path],
            fed_copy_or_move='move',
            metadata=metadata
        )

        # test resource has one file
        self.assertEqual(new_res.files.all().count(), 1,
                         msg="Number of content files is not equal to 1")
        self.assertEqual(new_res.resource_type, 'RasterResource')
        self.assertTrue(isinstance(new_res, GenericResource), type(new_res))
        self.assertTrue(new_res.metadata.title.value == 'My Test Raster Resource in User Zone')
        self.assertTrue(new_res.creator == self.user)
        self.assertTrue(new_res.short_id is not None, 'Short ID has not been created!')
        fed_path = '/{zone}/home/{user}'.format(zone=settings.HS_USER_IRODS_ZONE,
                                                user=settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
        self.assertEqual(new_res.resource_federation_path, fed_path)

    def test_add_files_to_resource_in_user_zone(self):
        pass

    def test_create_new_version_resource_in_user_zone(self):
        pass

    def test_delete_resource_in_user_zone(self):
        pass

    def test_folder_operations_in_user_zone(self):
        pass
