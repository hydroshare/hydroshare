import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.conf import settings

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import resource_file_add_process, resource_file_add_pre_process
from hs_core.views.utils import create_folder

from hs_core.testing import TestCaseCommonUtilities

from hs_file_types.models import GenericLogicalFile


class CompositeResourceTest(TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(CompositeResourceTest, self).setUp()
        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        super(CompositeResourceTest, self).create_irods_user_in_user_zone()

        self.raster_file_name = 'small_logan.tif'
        self.raster_file = 'hs_composite_resource/tests/data/{}'.format(self.raster_file_name)

        # transfer this valid tif file to user zone space for testing
        # only need to test that tif file stored in iRODS user zone space can be used to create a
        # composite resource and the file gets set to GenericLogicalFile type
        # Other relevant tests are adding a file to resource, deleting a file from resource
        # and deleting composite resource stored in iRODS user zone
        # Other detailed tests don't need to be retested for irods user zone space scenario since
        # as long as the tif file in iRODS user zone space can be read with metadata extracted
        # correctly, other functionalities are done with the same common functions regardless of
        # where the tif file comes from, either from local disk or from a federated user zone
        irods_target_path = '/' + settings.HS_USER_IRODS_ZONE + '/home/' + self.user.username + '/'
        file_list_dict = {self.raster_file: irods_target_path + self.raster_file_name}
        super(CompositeResourceTest, self).save_files_to_user_zone(file_list_dict)

    def tearDown(self):
        super(CompositeResourceTest, self).tearDown()
        super(CompositeResourceTest, self).assert_federated_irods_available()
        super(CompositeResourceTest, self).delete_irods_user_in_user_zone()

    def test_file_add_to_composite_resource(self):
        # only do federation testing when REMOTE_USE_IRODS is True and irods docker containers
        # are set up properly
        super(CompositeResourceTest, self).assert_federated_irods_available()

        # test that when we add file to an existing composite resource, the added file
        # automatically set to genericlogicalfile type
        self.assertEqual(BaseResource.objects.count(), 0)

        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Composite Resource With Files Added From Federated Zone',
            auto_aggregate=False
        )

        # there should not be any GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # add a file to the resource
        fed_test_file_full_path = '/{zone}/home/{username}/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, username=self.user.username,
            fname=self.raster_file_name)
        res_upload_files = []
        resource_file_add_pre_process(resource=self.composite_resource, files=res_upload_files,
                                      source_names=[fed_test_file_full_path], user=self.user,
                                      folder=None)
        resource_file_add_process(resource=self.composite_resource, files=res_upload_files,
                                  source_names=[fed_test_file_full_path], user=self.user,
                                  auto_aggregate=False)

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # create the generic aggregation (logical file)
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # check that the resource file is associated with GenericLogicalFile
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # there should be 1 GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        # test adding a file to a folder (Note the UI does not support uploading a iRODS file
        # to a specific folder)

        # create the folder
        new_folder = "my-new-folder"
        new_folder_path = os.path.join("data", "contents", new_folder)
        create_folder(self.composite_resource.short_id, new_folder_path)
        resource_file_add_pre_process(resource=self.composite_resource, files=res_upload_files,
                                      source_names=[fed_test_file_full_path], user=self.user,
                                      folder=new_folder)
        resource_file_add_process(resource=self.composite_resource, files=res_upload_files,
                                  source_names=[fed_test_file_full_path], user=self.user,
                                  folder=new_folder, auto_aggregate=False)

        self.assertEqual(self.composite_resource.files.all().count(), 2)

        self.composite_resource.delete()
