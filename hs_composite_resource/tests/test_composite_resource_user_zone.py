import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.conf import settings

from hs_core import hydroshare
from hs_core.models import BaseResource, ResourceFile
from hs_core.hydroshare.utils import resource_file_add_process, resource_file_add_pre_process
from hs_core.views.utils import create_folder, move_or_rename_file_or_folder

from hs_core.testing import TestCaseCommonUtilities

from hs_composite_resource.models import CompositeResource

from hs_file_types.models import GenericLogicalFile, GeoRasterLogicalFile


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

    def test_create_composite_resource_with_file_upload(self):
        # only do federation testing when REMOTE_USE_IRODS is True and irods docker containers
        # are set up properly
        super(CompositeResourceTest, self).assert_federated_irods_available()

        # test that when we create composite resource with an uploaded file, then the uploaded file
        # is automatically set to genericlogicalfile type
        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()

        # make sure composite_resource is created in federated user zone
        fed_path = '/{zone}/home/{user}'.format(zone=settings.HS_USER_IRODS_ZONE,
                                                user=settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
        self.assertEqual(self.composite_resource.resource_federation_path, fed_path)

        # Deprecated: there should not be any GenericLogicalFile object at this point
        # Issue 2456 Create composite with uploaded file now part of logical file
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

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
        self.composite_resource.delete()

    def test_generic_aggregation_xml_files_creation(self):
        """Test that aggregation metadata and map xml files are created on aggregation
        creation"""

        super(CompositeResourceTest, self).assert_federated_irods_available()

        self._create_composite_resource()
        # create a generic aggregation (logical file)
        self._create_generic_aggregation()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        istorage = self.composite_resource.get_irods_storage()
        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))

        self.composite_resource.delete()

    def test_generic_aggregation_xml_files_re_creation_on_file_rename_1(self):
        """Test that aggregation metadata and map xml files are recreated on aggregation
        name change - single file aggregation file rename where the aggregation is at the root
        of the storage folder hierarchy"""

        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()
        # create a generic aggregation (logical file)
        self._create_generic_aggregation()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        istorage = self.composite_resource.get_irods_storage()
        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))
        meta_xml_file_path = logical_file.metadata_file_path
        map_xml_file_path = logical_file.map_file_path
        base_file_name, ext = os.path.splitext(res_file.file_name)
        new_file_name = '{0}_1{1}'.format(base_file_name, ext)
        # rename the aggregation resource file -> causes aggregation rename
        # test the aggregation name after renaming the file
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = 'data/contents/{}'.format(new_file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        logical_file = res_file.logical_file
        # test that the aggregation metadata xml file was re-created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        # test that the aggregation map xml file was re-created
        self.assertTrue(istorage.exists(logical_file.map_file_path))
        # test that the old aggregation metadata xml file got deleted
        self.assertFalse(istorage.exists(meta_xml_file_path))
        # test that the old aggregation map xml file got deleted
        self.assertFalse(istorage.exists(map_xml_file_path))

        # test that the original meta xml file path and the current meta xml file path are different
        self.assertNotEqual(logical_file.metadata_file_path, meta_xml_file_path)
        # test that the original map xml file path and the current map xml file path are different
        self.assertNotEqual(logical_file.map_file_path, map_xml_file_path)
        self.composite_resource.delete()

    def test_generic_aggregation_xml_files_re_creation_on_file_rename_2(self):
        """Test that aggregation metadata and map xml files are recreated on aggregation
        name change - single file aggregation file rename where the aggregation is NOT at the root
        of the storage folder hierarchy"""

        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()

        res_file = self.composite_resource.files.first()
        # create a folder to move this file
        folder_name = 'generic'
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(folder_name, res_file.file_name)
        ResourceFile.create_folder(self.composite_resource, folder_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        # create a generic aggregation (logical file)
        self._create_generic_aggregation()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        istorage = self.composite_resource.get_irods_storage()
        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        expected_aggr_meta_file_path = "{root}/{folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=res_file.file_name)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))
        expected_aggr_map_file_path = "{root}/{folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=res_file.file_name)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)
        orig_meta_xml_file_path = logical_file.metadata_file_path
        orig_map_xml_file_path = logical_file.map_file_path

        # rename the aggregation resource file -> causes aggregation rename
        # test the aggregation name after renaming the file
        base_file_name, ext = os.path.splitext(res_file.file_name)
        new_file_name = '{0}_1{1}'.format(base_file_name, ext)
        src_path = 'data/contents/{0}/{1}'.format(folder_name, res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(folder_name, new_file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test that the aggregation metadata xml file was re-created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        expected_aggr_meta_file_path = "{root}/{folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=new_file_name)
        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        # test that the aggregation map xml file was re-created
        self.assertTrue(istorage.exists(logical_file.map_file_path))
        expected_aggr_map_file_path = "{root}/{folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=new_file_name)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)

        # test that the old aggregation metadata xml file got deleted
        self.assertFalse(istorage.exists(orig_meta_xml_file_path))
        # test that the old aggregation map xml file got deleted
        self.assertFalse(istorage.exists(orig_map_xml_file_path))

        # test that the original meta xml file path and the current meta xml file path are different
        self.assertNotEqual(logical_file.metadata_file_path, orig_meta_xml_file_path)
        # test that the original map xml file path and the current map xml file path are different
        self.assertNotEqual(logical_file.map_file_path, orig_map_xml_file_path)
        self.composite_resource.delete()

    def test_generic_aggregation_xml_files_re_creation_on_file_move(self):
        """Test that aggregation metadata and map xml files are recreated when a resource file
        that is part of the generic aggregation is moved """

        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()

        # create a generic aggregation (logical file)
        self._create_generic_aggregation()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        istorage = self.composite_resource.get_irods_storage()
        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        expected_aggr_meta_file_path = "{root}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, fn=res_file.file_name)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))
        expected_aggr_map_file_path = "{root}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, fn=res_file.file_name)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)
        # hold on to original xml file paths to test that they get deleted
        orig_meta_xml_file_path = logical_file.metadata_file_path
        orig_map_xml_file_path = logical_file.map_file_path

        # create a folder to move this file
        folder_name = 'generic'
        ResourceFile.create_folder(self.composite_resource, folder_name)
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(folder_name, res_file.file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file

        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        expected_aggr_meta_file_path = "{root}/{folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=res_file.file_name)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))
        expected_aggr_map_file_path = "{root}/{folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=res_file.file_name)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)

        # test that the old aggregation metadata xml file got deleted
        self.assertFalse(istorage.exists(orig_meta_xml_file_path))
        # test that the old aggregation map xml file got deleted
        self.assertFalse(istorage.exists(orig_map_xml_file_path))

        # test that the original meta xml file path and the current meta xml file path are different
        self.assertNotEqual(logical_file.metadata_file_path, orig_meta_xml_file_path)
        # test that the original map xml file path and the current map xml file path are different
        self.assertNotEqual(logical_file.map_file_path, orig_map_xml_file_path)
        self.composite_resource.delete()

    def test_generic_aggregation_xml_files_re_creation_on_folder_rename(self):
        """Test that aggregation metadata and map xml files are recreated when a folder containing
        a resource file that is part of the generic aggregation is renamed """

        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()

        res_file = self.composite_resource.files.first()
        # create a folder to move this file
        folder_name = 'generic'
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(folder_name, res_file.file_name)
        ResourceFile.create_folder(self.composite_resource, folder_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        # create a generic aggregation (logical file)
        self._create_generic_aggregation()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        istorage = self.composite_resource.get_irods_storage()
        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        expected_aggr_meta_file_path = "{root}/{folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=res_file.file_name)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))
        expected_aggr_map_file_path = "{root}/{folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=res_file.file_name)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)

        # hold on to the original xml file paths to test that they get deleted
        orig_meta_xml_file_path = logical_file.metadata_file_path
        orig_map_xml_file_path = logical_file.map_file_path

        # now change the folder name 'generic' to 'generic_1'
        folder_rename = '{}_1'.format(folder_name)
        src_path = 'data/contents/{}'.format(folder_name)
        tgt_path = 'data/contents/{}'.format(folder_rename)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        expected_aggr_meta_file_path = "{root}/{folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, folder=folder_rename, fn=res_file.file_name)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))
        expected_aggr_map_file_path = "{root}/{folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, folder=folder_rename, fn=res_file.file_name)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)

        # test that the old aggregation metadata xml file got deleted
        self.assertFalse(istorage.exists(orig_meta_xml_file_path))
        # test that the old aggregation map xml file got deleted
        self.assertFalse(istorage.exists(orig_map_xml_file_path))

        # test that the original meta xml file path and the current meta xml file path are different
        self.assertNotEqual(logical_file.metadata_file_path, orig_meta_xml_file_path)
        # test that the original map xml file path and the current map xml file path are different
        self.assertNotEqual(logical_file.map_file_path, orig_map_xml_file_path)
        self.composite_resource.delete()

    def test_generic_aggregation_xml_files_re_creation_on_folder_move(self):
        """Test that aggregation metadata and map xml files are recreated when a folder containing
        a resource file that is part of the generic aggregation is moved """

        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()

        res_file = self.composite_resource.files.first()
        # create a folder to contain the aggregation file
        folder_name = 'generic_2'
        ResourceFile.create_folder(self.composite_resource, folder_name)
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(folder_name, res_file.file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        # create a generic aggregation (logical file)
        self._create_generic_aggregation()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        istorage = self.composite_resource.get_irods_storage()
        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        expected_aggr_meta_file_path = "{root}/{folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=res_file.file_name)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))
        expected_aggr_map_file_path = "{root}/{folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=res_file.file_name)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)

        # hold on to the original xml file paths to test that they get deleted
        orig_meta_xml_file_path = logical_file.metadata_file_path
        orig_map_xml_file_path = logical_file.map_file_path

        # create a folder where we will move the 'generic_2' folder that contains the
        # aggregation file
        parent_folder = 'generic_1'
        ResourceFile.create_folder(self.composite_resource, parent_folder)
        # now move 'generic_2' to folder 'generic_1'
        src_path = 'data/contents/{}'.format(folder_name)
        tgt_path = 'data/contents/{0}/{1}'.format(parent_folder, folder_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        expected_aggr_meta_file_path = "{root}/{folder_1}/{folder_2}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, folder_1=parent_folder, folder_2=folder_name,
            fn=res_file.file_name)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))
        expected_aggr_map_file_path = "{root}/{folder_1}/{folder_2}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, folder_1=parent_folder, folder_2=folder_name,
            fn=res_file.file_name)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)

        # test that the old aggregation metadata xml file got deleted
        self.assertFalse(istorage.exists(orig_meta_xml_file_path))
        # test that the old aggregation map xml file got deleted
        self.assertFalse(istorage.exists(orig_map_xml_file_path))

        # test that the original meta xml file path and the current meta xml file path are different
        self.assertNotEqual(logical_file.metadata_file_path, orig_meta_xml_file_path)
        # test that the original map xml file path and the current map xml file path are different
        self.assertNotEqual(logical_file.map_file_path, orig_map_xml_file_path)
        self.composite_resource.delete()

    def test_generic_aggregation_xml_files_delete_1(self):
        """Test that aggregation metadata and map xml files are deleted on aggregation
        delete"""

        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()

        # create a generic aggregation (logical file)
        self._create_generic_aggregation()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        istorage = self.composite_resource.get_irods_storage()
        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))

        meta_xml_file_path = logical_file.metadata_file_path
        map_xml_file_path = logical_file.map_file_path
        # remove aggregation
        logical_file.remove_aggregation()
        # test that the aggregation metadata xml file got deleted
        self.assertFalse(istorage.exists(meta_xml_file_path))
        # test that the aggregation map xml file got deleted
        self.assertFalse(istorage.exists(map_xml_file_path))
        self.composite_resource.delete()

    def test_generic_aggregation_xml_files_delete_2(self):
        """Test that aggregation metadata and map xml files are deleted on deleting res file
        that is part of a generic aggregation"""

        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()

        # create a generic aggregation (logical file)
        self._create_generic_aggregation()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        istorage = self.composite_resource.get_irods_storage()
        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))

        meta_xml_file_path = logical_file.metadata_file_path
        map_xml_file_path = logical_file.map_file_path
        # delete res file
        hydroshare.delete_resource_file(self.composite_resource.short_id, res_file.id,
                                        self.user)
        self.assertEqual(self.composite_resource.files.all().count(), 0)
        # test that the aggregation metadata xml file got deleted
        self.assertFalse(istorage.exists(meta_xml_file_path))
        # test that the aggregation map xml file got deleted
        self.assertFalse(istorage.exists(map_xml_file_path))
        self.composite_resource.delete()

    def test_multi_file_aggregation_xml_files_creation_1(self):
        """Test that aggregation metadata and map xml files are created when a multi file
        aggregation (using raster here) is created - aggregation folder at the root of the folder
        hierarchy"""

        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()
        # create a folder and move the raster file there
        folder_name = 'raster'
        ResourceFile.create_folder(self.composite_resource, folder_name)
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(folder_name, res_file.file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        # create a raster aggregation (logical file)
        self._create_raster_aggregation()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        istorage = self.composite_resource.get_irods_storage()
        # test that the aggregation metadata xml file was created
        expected_aggr_meta_file_path = "{root}/{folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=folder_name)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        # test that the aggregation map xml file was created
        expected_aggr_map_file_path = "{root}/{folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=folder_name)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)
        self.assertTrue(istorage.exists(logical_file.map_file_path))

        self.composite_resource.delete()

    def test_multi_file_aggregation_xml_files_creation_2(self):
        """Test that aggregation metadata and map xml files are created when a multi file
        aggregation (using raster here) is created - aggregation folder NOT at the root of
        the folder hierarchy - aggregation folder has a parent folder"""

        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()
        # create a folder and move the raster file there
        parent_folder = 'my_folder'
        child_folder = 'raster'
        folder_path = '{0}/{1}'.format(parent_folder, child_folder)
        ResourceFile.create_folder(self.composite_resource, folder_path)
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(folder_path, res_file.file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        # create a raster aggregation (logical file)
        self._create_raster_aggregation()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        istorage = self.composite_resource.get_irods_storage()
        # test that the aggregation metadata xml file was created
        expected_aggr_meta_file_path = "{root}/{p_folder}/{c_folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, p_folder=parent_folder, c_folder=child_folder,
            fn=child_folder)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        # test that the aggregation map xml file was created
        expected_aggr_map_file_path = "{root}/{p_folder}/{c_folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, p_folder=parent_folder, c_folder=child_folder,
            fn=child_folder)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)
        self.assertTrue(istorage.exists(logical_file.map_file_path))

        self.composite_resource.delete()

    def test_multi_file_aggregation_xml_files_re_creation_on_folder_rename_1(self):
        """Test that aggregation metadata and map xml files are re-created on multi-file
        aggregation (using raster here) folder name change - aggregation folder at the root of
        the folder hierarchy"""

        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()
        # create a folder and move the raster file there
        folder_name = 'raster'
        ResourceFile.create_folder(self.composite_resource, folder_name)
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(folder_name, res_file.file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        # create a raster aggregation (logical file)
        self._create_raster_aggregation()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        istorage = self.composite_resource.get_irods_storage()
        # test that the aggregation metadata xml file was created
        expected_aggr_meta_file_path = "{root}/{folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=folder_name)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        # test that the aggregation map xml file was created
        expected_aggr_map_file_path = "{root}/{folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=folder_name)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)
        self.assertTrue(istorage.exists(logical_file.map_file_path))

        # hold on to the original xml file paths to test that they get deleted
        orig_meta_xml_file_path = logical_file.metadata_file_path
        orig_map_xml_file_path = logical_file.map_file_path
        # now change the folder name 'raster' to 'raster_1'
        folder_rename = '{}_1'.format(folder_name)
        src_path = 'data/contents/{}'.format(folder_name)
        tgt_path = 'data/contents/{}'.format(folder_rename)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        expected_aggr_meta_file_path = "{root}/{folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, folder=folder_rename, fn=folder_rename)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))
        expected_aggr_map_file_path = "{root}/{folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, folder=folder_rename, fn=folder_rename)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)

        # test that the old aggregation metadata xml file got deleted
        self.assertFalse(istorage.exists(orig_meta_xml_file_path))
        # test that the old aggregation map xml file got deleted
        self.assertFalse(istorage.exists(orig_map_xml_file_path))

        # test that the original meta xml file path and the current meta xml file path are different
        self.assertNotEqual(logical_file.metadata_file_path, orig_meta_xml_file_path)
        # test that the original map xml file path and the current map xml file path are different
        self.assertNotEqual(logical_file.map_file_path, orig_map_xml_file_path)

        self.composite_resource.delete()

    def test_raster_aggregation_xml_files_re_creation_on_folder_rename_2(self):
        """Test that aggregation metadata and map xml files are re-created on multi-file
        aggregation (using raster here) folder name change - aggregation folder NOT at the root of
        the folder hierarchy - aggregation folder has a parent folder"""

        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()
        # create a folder and move the raster file there
        parent_folder = 'my_folder'
        child_folder = 'raster'
        folder_path = '{0}/{1}'.format(parent_folder, child_folder)
        ResourceFile.create_folder(self.composite_resource, folder_path)
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(folder_path, res_file.file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        # create a raster aggregation (logical file)
        self._create_raster_aggregation()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        istorage = self.composite_resource.get_irods_storage()
        # test that the aggregation metadata xml file was created
        expected_aggr_meta_file_path = "{root}/{p_folder}/{c_folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, p_folder=parent_folder, c_folder=child_folder,
            fn=child_folder)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        # test that the aggregation map xml file was created
        expected_aggr_map_file_path = "{root}/{p_folder}/{c_folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, p_folder=parent_folder, c_folder=child_folder,
            fn=child_folder)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)
        self.assertTrue(istorage.exists(logical_file.map_file_path))

        # hold on to the original xml file paths to test that they get deleted
        orig_meta_xml_file_path = logical_file.metadata_file_path
        orig_map_xml_file_path = logical_file.map_file_path
        # now change the folder name 'raster' to 'raster_1'
        src_path = 'data/contents/{0}/{1}'.format(parent_folder, child_folder)
        child_folder_rename = '{}_1'.format(child_folder)
        tgt_path = 'data/contents/{0}/{1}'.format(parent_folder, child_folder_rename)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        expected_aggr_meta_file_path = "{root}/{p_folder}/{c_folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, p_folder=parent_folder,
            c_folder=child_folder_rename, fn=child_folder_rename)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))
        expected_aggr_map_file_path = "{root}/{p_folder}/{c_folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, p_folder=parent_folder,
            c_folder=child_folder_rename, fn=child_folder_rename)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)

        # test that the old aggregation metadata xml file got deleted
        self.assertFalse(istorage.exists(orig_meta_xml_file_path))
        # test that the old aggregation map xml file got deleted
        self.assertFalse(istorage.exists(orig_map_xml_file_path))

        # test that the original meta xml file path and the current meta xml file path are different
        self.assertNotEqual(logical_file.metadata_file_path, orig_meta_xml_file_path)
        # test that the original map xml file path and the current map xml file path are different
        self.assertNotEqual(logical_file.map_file_path, orig_map_xml_file_path)

        self.composite_resource.delete()

    def test_raster_aggregation_xml_files_re_creation_on_folder_move_1(self):
        """Test that aggregation metadata and map xml files are re-created on raster aggregation
        folder move - raster folder at the root before move"""

        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()
        # create a folder and move the raster file there
        folder_name = 'raster'
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(folder_name, res_file.file_name)
        ResourceFile.create_folder(self.composite_resource, folder_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        # create a raster aggregation (logical file)
        self._create_raster_aggregation()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        istorage = self.composite_resource.get_irods_storage()
        # test that the aggregation metadata xml file was created
        expected_aggr_meta_file_path = "{root}/{folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=folder_name)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        # test that the aggregation map xml file was created
        expected_aggr_map_file_path = "{root}/{folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, folder=folder_name, fn=folder_name)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)
        self.assertTrue(istorage.exists(logical_file.map_file_path))

        # create a folder and move the raster folder there
        parent_folder = 'raster_parent'
        ResourceFile.create_folder(self.composite_resource, parent_folder)

        # now move the 'raster' folder to 'raster_parent'
        src_path = 'data/contents/{}'.format(folder_name)
        tgt_path = 'data/contents/{0}/{1}'.format(parent_folder, folder_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        expected_aggr_meta_file_path = "{root}/{p_folder}/{c_folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, p_folder=parent_folder, c_folder=folder_name,
            fn=folder_name)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))
        expected_aggr_map_file_path = "{root}/{p_folder}/{c_folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, p_folder=parent_folder, c_folder=folder_name,
            fn=folder_name)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)

        self.composite_resource.delete()

    def test_raster_aggregation_xml_files_re_creation_on_folder_move_2(self):
        """Test that aggregation metadata and map xml files are re-created on raster aggregation
        parent folder move - raster folder not at the root before move"""

        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()
        # create a folder and move the raster file there
        parent_folder = 'raster_parent'
        folder_name = 'raster'
        folder_path = '{0}/{1}'.format(parent_folder, folder_name)
        ResourceFile.create_folder(self.composite_resource, folder_path)
        src_path = 'data/contents/{}'.format(res_file.file_name)
        tgt_path = 'data/contents/{0}/{1}'.format(folder_path, res_file.file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        # create a raster aggregation (logical file)
        self._create_raster_aggregation()
        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        istorage = self.composite_resource.get_irods_storage()
        # test that the aggregation metadata xml file was created
        expected_aggr_meta_file_path = "{root}/{p_folder}/{c_folder}/{fn}_meta.xml".format(
            root=self.composite_resource.file_path, p_folder=parent_folder, c_folder=folder_name,
            fn=folder_name)

        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))
        # test that the aggregation map xml file was created
        expected_aggr_map_file_path = "{root}/{p_folder}/{c_folder}/{fn}_resmap.xml".format(
            root=self.composite_resource.file_path, p_folder=parent_folder, c_folder=folder_name,
            fn=folder_name)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)
        self.assertTrue(istorage.exists(logical_file.map_file_path))

        # create a folder and move the raster parent folder there
        root_folder = 'raster_super_parent'
        ResourceFile.create_folder(self.composite_resource, root_folder)

        # now move the 'raster_parent' folder to 'raster_super_parent'
        src_path = 'data/contents/{}'.format(parent_folder)
        tgt_path = 'data/contents/{0}/{1}'.format(root_folder, parent_folder)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        res_file = self.composite_resource.files.first()
        logical_file = res_file.logical_file
        # test that the aggregation metadata xml file was created
        self.assertTrue(istorage.exists(logical_file.metadata_file_path))

        expected_aggr_meta_file_path = "{root}/{r_folder}/{p_folder}/{c_folder}/{fn}_meta.xml"
        expected_aggr_meta_file_path = expected_aggr_meta_file_path.format(
            root=self.composite_resource.file_path,
            r_folder=root_folder, p_folder=parent_folder, c_folder=folder_name, fn=folder_name)
        self.assertEqual(logical_file.metadata_file_path, expected_aggr_meta_file_path)
        # test that the aggregation map xml file was created
        self.assertTrue(istorage.exists(logical_file.map_file_path))

        expected_aggr_map_file_path = "{root}/{r_folder}/{p_folder}/{c_folder}/{fn}_resmap.xml"
        expected_aggr_map_file_path = expected_aggr_map_file_path.format(
            root=self.composite_resource.file_path,
            r_folder=root_folder, p_folder=parent_folder, c_folder=folder_name, fn=folder_name)
        self.assertEqual(logical_file.map_file_path, expected_aggr_map_file_path)

        self.composite_resource.delete()

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
            title='Test Composite Resource Federated',
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

    def test_file_delete_composite_resource(self):
        # only do federation testing when REMOTE_USE_IRODS is True and irods docker containers
        # are set up properly
        super(CompositeResourceTest, self).assert_federated_irods_available()

        self._create_composite_resource()
        res_file = self.composite_resource.files.first()
        # create the generic aggregation (logical file)
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        # there should be one GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        hydroshare.delete_resource_file(self.composite_resource.short_id, res_file.id,
                                        self.user)
        self.assertEqual(self.composite_resource.files.all().count(), 0)
        # there should not be any GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        self.composite_resource.delete()

    def test_delete_composite_resource(self):
        # only do federation testing when REMOTE_USE_IRODS is True and irods docker containers
        # are set up properly
        super(CompositeResourceTest, self).assert_federated_irods_available()

        self.assertEqual(BaseResource.objects.count(), 0)
        self._create_composite_resource()
        res_file = self.composite_resource.files.first()
        # create the generic aggregation (logical file)
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        self.assertEqual(BaseResource.objects.count(), 1)
        self.composite_resource.delete()
        self.assertEqual(BaseResource.objects.count(), 0)
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

    def test_copy_composite_resource_with_single_file_aggregation(self):
        # test that we can create a copy of a composite resource that has a single file
        # aggregation

        self._test_copy_or_version_of_composite_resource(aggr_type=GenericLogicalFile,
                                                         action='copy')

    def test_copy_composite_resource_with_multi_file_aggregation(self):
        # test that we can create a copy of a composite resource that has one multi-file aggregation

        self._test_copy_or_version_of_composite_resource(aggr_type=GeoRasterLogicalFile,
                                                         action='copy')

    def test_version_composite_resource_with_single_file_aggregation(self):
        # test that we can create a new version of a composite resource that has a single file
        # aggregation

        self._test_copy_or_version_of_composite_resource(aggr_type=GenericLogicalFile,
                                                         action='version')

    def test_version_composite_resource_with_multi_file_aggregation(self):
        # test that we can create a new version of a composite resource that has one
        # multi-file aggregation

        self._test_copy_or_version_of_composite_resource(aggr_type=GeoRasterLogicalFile,
                                                         action='version')

    def _create_composite_resource(self):
        fed_test_file_full_path = '/{zone}/home/{username}/{fname}'.format(
            zone=settings.HS_USER_IRODS_ZONE, username=self.user.username,
            fname=self.raster_file_name)
        res_upload_files = []
        fed_res_path = hydroshare.utils.get_federated_zone_home_path(fed_test_file_full_path)
        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Federated Composite Resource Testing',
            files=res_upload_files,
            source_names=[fed_test_file_full_path],
            fed_res_path=fed_res_path,
            move=False,
            metadata=[],
            auto_aggregate=False
        )

    def _create_generic_aggregation(self):
        # make sure composite_resource is created in federated user zone
        fed_path = '/{zone}/home/{user}'.format(zone=settings.HS_USER_IRODS_ZONE,
                                                user=settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
        self.assertEqual(self.composite_resource.resource_federation_path, fed_path)
        res_file = self.composite_resource.files.first()
        # create the generic aggregation (logical file)
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

    def _create_raster_aggregation(self):
        # make sure composite_resource is created in federated user zone
        fed_path = '/{zone}/home/{user}'.format(zone=settings.HS_USER_IRODS_ZONE,
                                                user=settings.HS_LOCAL_PROXY_USER_IN_FED_ZONE)
        self.assertEqual(self.composite_resource.resource_federation_path, fed_path)
        res_file = self.composite_resource.files.first()
        # create the raster aggregation (logical file)
        if res_file.file_folder is None:
            GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user,
                                               file_id=res_file.id)
        else:
            GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user,
                                               folder_path=res_file.file_folder)

    def _test_copy_or_version_of_composite_resource(self, aggr_type,  action):
        self._create_composite_resource()
        self.assertEqual(CompositeResource.objects.all().count(), 1)
        # create the specified aggregation (logical file)
        if aggr_type == GenericLogicalFile:
            self._create_generic_aggregation()
        else:
            self._create_raster_aggregation()

        self.assertEqual(aggr_type.objects.all().count(), 1)
        new_res_composite = hydroshare.create_empty_resource(self.composite_resource.short_id,
                                                             self.user,
                                                             action=action)
        new_res_composite = hydroshare.copy_resource(self.composite_resource, new_res_composite)
        self.assertEqual(CompositeResource.objects.all().count(), 2)
        self.assertEqual(self.composite_resource.files.count(), new_res_composite.files.count())
        self.assertEqual(len(self.composite_resource.logical_files),
                         len(new_res_composite.logical_files))
        self.assertEqual(aggr_type.objects.all().count(), 2)
        istorage = new_res_composite.get_irods_storage()
        for logical_file in new_res_composite.logical_files:
            # test that the aggregation metadata xml file was created
            self.assertTrue(istorage.exists(logical_file.metadata_file_path))
            # test that the aggregation map xml file was created
            self.assertTrue(istorage.exists(logical_file.map_file_path))

        new_res_composite.delete()
        self.composite_resource.delete()
