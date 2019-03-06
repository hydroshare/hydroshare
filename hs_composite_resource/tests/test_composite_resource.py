# coding=utf-8
import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from rest_framework import status

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.models import BaseResource, ResourceFile
from hs_core.hydroshare.utils import resource_file_add_process, get_resource_by_shortkey
from hs_core.views.utils import create_folder, move_or_rename_file_or_folder, remove_folder, \
    unzip_file, add_reference_url_to_resource, edit_reference_url_in_resource
from hs_composite_resource.models import CompositeResource
from hs_file_types.models import GenericLogicalFile, GeoRasterLogicalFile, GenericFileMetaData, \
    RefTimeseriesLogicalFile, FileSetLogicalFile, NetCDFLogicalFile, TimeSeriesLogicalFile, \
    GeoFeatureLogicalFile
from hs_file_types.tests.utils import CompositeResourceTestMixin


class CompositeResourceTest(MockIRODSTestCaseMixin, TransactionTestCase,
                            CompositeResourceTestMixin):
    def setUp(self):
        super(CompositeResourceTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.res_title = 'Testing Composite Resource'
        self.invalid_url = "http://i.am.invalid"
        self.valid_url = "https://www.google.com"
        self.raster_file_name = 'small_logan.tif'
        self.raster_file = 'hs_composite_resource/tests/data/{}'.format(self.raster_file_name)
        self.generic_file_name = 'generic_file.txt'
        self.generic_file = 'hs_composite_resource/tests/data/{}'.format(self.generic_file_name)
        self.netcdf_file_name = 'netcdf_valid.nc'
        self.netcdf_file = 'hs_composite_resource/tests/data/{}'.format(self.netcdf_file_name)
        self.sqlite_file_name = 'ODM2.sqlite'
        self.sqlite_file = 'hs_composite_resource/tests/data/{}'.format(self.sqlite_file_name)
        self.watershed_dbf_file_name = 'watersheds.dbf'
        self.watershed_dbf_file = 'hs_composite_resource/tests/data/{}'.format(
            self.watershed_dbf_file_name)
        self.watershed_shp_file_name = 'watersheds.shp'
        self.watershed_shp_file = 'hs_composite_resource/tests/data/{}'.format(
            self.watershed_shp_file_name)
        self.watershed_shx_file_name = 'watersheds.shx'
        self.watershed_shx_file = 'hs_composite_resource/tests/data/{}'.format(
            self.watershed_shx_file_name)
        self.json_file_name = 'multi_sites_formatted_version1.0.refts.json'
        self.json_file = 'hs_composite_resource/tests/data/{}'.format(
            self.json_file_name)
        self.zip_file_name = 'test.zip'
        self.zip_file = 'hs_composite_resource/tests/data/{}'.format(self.zip_file_name)
        self.zipped_aggregation_file_name = 'multi_sites_formatted_version1.0.refts.zip'
        self.zipped_aggregation_file = \
            'hs_composite_resource/tests/data/{}'.format(self.zipped_aggregation_file_name)

    def tearDown(self):
        super(CompositeResourceTest, self).tearDown()
        if self.composite_resource:
            self.composite_resource.delete()

    def test_create_composite_resource(self):
        # test that we can create a composite resource

        # there should not be any resource at this point
        self.assertEqual(BaseResource.objects.count(), 0)
        self.create_composite_resource()

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")

    def test_create_composite_resource_with_file_upload(self):
        # test that when we create composite resource with an uploaded file, then the uploaded file
        # is automatically not set to genericlogicalfile type

        self.assertEqual(BaseResource.objects.count(), 0)

        self.create_composite_resource(self.raster_file)
        # There should not be a GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # there should be no GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # there should be no GenericFileMetaData object at this point
        self.assertEqual(GenericFileMetaData.objects.count(), 0)
        self.composite_resource.delete()

        # there should be no GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # there should be no GenericFileMetaData object at this point
        self.assertEqual(GenericFileMetaData.objects.count(), 0)
        # setting resource to None to avoid deleting resource again in tearDown() since we have
        # deleted the resource already
        self.composite_resource = None

    def test_add_and_edit_referenced_url(self):
        # test that referenced url can be added to composite resource as a genericlogical file
        # type single file aggregation, and can also be edited

        # there should not be any resource at this point
        self.assertEqual(BaseResource.objects.count(), 0)

        # test invalid url fails to be added to an empty composite resource
        self.create_composite_resource()
        url_file_base_name = 'test_url_invalid'
        ret_status, msg, _ = add_reference_url_to_resource(self.user,
                                                           self.composite_resource.short_id,
                                                           self.invalid_url, url_file_base_name,
                                                           'data/contents')
        self.assertEqual(ret_status, status.HTTP_400_BAD_REQUEST,
                         msg='Invalid referenced URL should not be added to resource if '
                             'validate_url_flag is True')

        # test invalid url CAN be added to the resource if validate_url_flag is turned off
        ret_status, msg, _ = add_reference_url_to_resource(self.user,
                                                           self.composite_resource.short_id,
                                                           self.invalid_url, url_file_base_name,
                                                           'data/contents',
                                                           validate_url_flag=False)
        self.assertEqual(ret_status, status.HTTP_200_OK,
                         msg='Invalid referenced URL should be added to resource if '
                             'validate_url_flag is False')
        self.assertEqual(self.composite_resource.files.count(), 1)
        # there should be one GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        res_file = self.composite_resource.files.first()
        # url singlefile aggregation should have extra_data url field created
        url_logical_file = res_file.logical_file
        self.assertEqual(url_logical_file.extra_data['url'], self.invalid_url)

        # delete the invalid_url resource file
        hydroshare.delete_resource_file(self.composite_resource.short_id,
                                        res_file.id, self.user)
        self.assertEqual(self.composite_resource.files.count(), 0)
        # there should be no GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # test valid url can be added to an empty composite resource
        url_file_base_name = 'test_url_valid'
        ret_status, msg, _ = add_reference_url_to_resource(self.user,
                                                           self.composite_resource.short_id,
                                                           self.valid_url, url_file_base_name,
                                                           'data/contents')
        self.assertEqual(ret_status, status.HTTP_200_OK,
                         msg='Valid URL should be added to resource')
        self.assertEqual(self.composite_resource.files.count(), 1)
        # there should be one GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        # test valid url can be added to a subfolder of a composite resource
        new_folder_path = os.path.join("data", "contents", "my-new-folder")
        create_folder(self.composite_resource.short_id, new_folder_path)
        ret_status, msg, _ = add_reference_url_to_resource(self.user,
                                                           self.composite_resource.short_id,
                                                           self.valid_url, url_file_base_name,
                                                           new_folder_path)
        self.assertEqual(ret_status, status.HTTP_200_OK)
        self.assertEqual(self.composite_resource.files.count(), 2)
        # there should be two GenericLogicalFile objects at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 2)
        for res_file in self.composite_resource.files.all():
            # url singlefile aggregation should have extra_data url field created
            url_logical_file = res_file.logical_file
            self.assertEqual(url_logical_file.extra_data['url'], self.valid_url)

        # remove new_folder_path
        remove_folder(self.user, self.composite_resource.short_id, new_folder_path)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # test edit reference url
        new_ref_url = self.invalid_url
        url_filename = url_file_base_name + '.url'
        ret_status, msg = edit_reference_url_in_resource(self.user, self.composite_resource,
                                                         new_ref_url, 'data/contents',
                                                         url_filename)
        self.assertEqual(ret_status, status.HTTP_400_BAD_REQUEST, msg='Referenced URL should not '
                                                                      'be updated with invalid URL '
                                                                      'when validate_url_flag is '
                                                                      'True')

        # test resource referenced URL CAN be updated with an invalid url if validate_url_flag is
        # set to False
        ret_status, msg = edit_reference_url_in_resource(self.user,
                                                         self.composite_resource,
                                                         new_ref_url,
                                                         'data/contents',
                                                         url_filename,
                                                         validate_url_flag=False)
        self.assertEqual(ret_status, status.HTTP_200_OK,
                         msg='Referenced URL should be updated with invalid URL when '
                             'validate_url_flag is False')
        res_file = self.composite_resource.files.all().first()
        url_logical_file = res_file.logical_file
        self.assertEqual(url_logical_file.extra_data['url'], new_ref_url)

        # test resource referenced URL can be updated with a valid URL
        new_ref_url = 'https://www.yahoo.com'
        ret_status, msg = edit_reference_url_in_resource(self.user, self.composite_resource,
                                                         new_ref_url, 'data/contents',
                                                         url_filename)
        self.assertEqual(ret_status, status.HTTP_200_OK)
        self.assertEqual(self.composite_resource.files.count(), 1)
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        res_file = self.composite_resource.files.all().first()
        url_logical_file = res_file.logical_file
        self.assertEqual(url_logical_file.extra_data['url'], new_ref_url)

    def test_add_file_to_composite_resource(self):
        # test that when we add file to an existing composite resource, the added file
        # is not automatically set to genericlogicalfile type

        self.create_composite_resource(self.raster_file)

        # there should not be any GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)
        # there should be 0 GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

    def test_aggregation_folder_delete(self):
        # here we are testing that when a folder is deleted containing
        # files for a logical file type, other files in the composite resource are still associated
        # with their respective logical file types

        self.create_composite_resource(self.raster_file)

        tif_res_file = [f for f in self.composite_resource.files.all()
                        if f.extension == ".tif"][0]

        # add a generic file type
        self.add_file_to_resource(file_to_add=self.generic_file)

        # there should be no GenericLogicalFile objects
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # there should not be any GeoRasterLogicalFile object
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, tif_res_file.id)
        # there should be no GenericLogicalFile objects
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # there should be 1 GeoRasterLogicalFile object
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        txt_res_file = [f for f in self.composite_resource.files.all()
                        if f.extension == ".txt"][0]

        # set generic logical file
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, txt_res_file.id)
        txt_res_file = [f for f in self.composite_resource.files.all()
                        if f.extension == ".txt"][0]
        self.assertEqual(txt_res_file.logical_file_type_name, "GenericLogicalFile")

        # now delete the folder small_logan that contains files associated with raster file type
        folder_path = "data/contents/small_logan"
        remove_folder(self.user, self.composite_resource.short_id, folder_path)
        txt_res_file.refresh_from_db()
        self.assertEqual(txt_res_file.logical_file_type_name, "GenericLogicalFile")
        # there should not be any GeoRasterLogicalFile object
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # there should be 1 GenericLogicalFile objects
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

    def test_core_metadata_CRUD(self):
        """test that all core metadata elements work for this resource type"""

        self.create_composite_resource()
        # test current metadata status of the composite resource

        # there should be title element
        self.assertEqual(self.composite_resource.metadata.title.value, "Testing Composite Resource")
        # there shouldn't be abstract element
        self.assertEqual(self.composite_resource.metadata.description, None)
        # there shouldn't be any format element
        self.assertEqual(self.composite_resource.metadata.formats.count(), 0)
        # there should be date element - 2 elements
        self.assertEqual(self.composite_resource.metadata.dates.count(), 2)
        # there should be 1 creator element
        self.assertEqual(self.composite_resource.metadata.creators.count(), 1)
        # there should not be any contributor element
        self.assertEqual(self.composite_resource.metadata.contributors.count(), 0)
        # there should not be any coverage element
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 0)
        # there should not be any funding agency element
        self.assertEqual(self.composite_resource.metadata.funding_agencies.count(), 0)
        # there should be 1 identifier element
        self.assertEqual(self.composite_resource.metadata.identifiers.count(), 1)
        # there should be 1 language element
        self.assertNotEqual(self.composite_resource.metadata.language, None)
        # there should not be any publisher element
        self.assertEqual(self.composite_resource.metadata.publisher, None)
        # there should not be any format element
        self.assertEqual(self.composite_resource.metadata.formats.count(), 0)
        # there should not be any relation element
        self.assertEqual(self.composite_resource.metadata.relations.count(), 0)
        # there should be 1 rights element
        self.assertNotEqual(self.composite_resource.metadata.rights, None)
        # there shouldn't be any source element
        self.assertEqual(self.composite_resource.metadata.sources.count(), 0)
        # there should not be any subject elements
        self.assertEqual(self.composite_resource.metadata.subjects.count(), 0)
        # there should be 1 type element
        self.assertNotEqual(self.composite_resource.metadata.type, None)
        # there should not be any key/value metadata
        self.assertEqual(self.composite_resource.extra_metadata, {})

        # test create metadata

        # create abstract
        metadata = self.composite_resource.metadata
        metadata.create_element('description', abstract='new abstract for the resource')
        # there should be abstract element
        self.assertNotEqual(self.composite_resource.metadata.description, None)
        # add a file to the resource to auto create format element
        self.raster_file_obj = open(self.raster_file, 'r')
        resource_file_add_process(resource=self.composite_resource,
                                  files=(self.raster_file_obj,), user=self.user,
                                  auto_aggregate=False)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        # now there should be 1 format element
        self.assertEqual(self.composite_resource.metadata.formats.count(), 1)
        # add another creator
        metadata.create_element('creator', name='John Smith')
        # there should be 2 creators now
        self.assertEqual(self.composite_resource.metadata.creators.count(), 2)
        # add a contributor
        metadata.create_element('contributor', name='Lisa Smith')
        # there should be 1 contributor now
        self.assertEqual(self.composite_resource.metadata.contributors.count(), 1)
        # add a period type coverage
        value_dict = {'name': 'Name for period coverage', 'start': '1/1/2000', 'end': '12/12/2012'}
        metadata.create_element('coverage', type='period', value=value_dict)
        # add a point type coverage
        value_dict = {'east': '56.45678', 'north': '12.6789', 'units': 'decimal deg'}
        metadata.create_element('coverage', type='point', value=value_dict)
        # there should be 2 coverage elements now
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 2)
        cov_pt = self.composite_resource.metadata.coverages.all().filter(type='point').first()
        self.assertNotEqual(cov_pt, None)
        cov_period = self.composite_resource.metadata.coverages.all().filter(type='period').first()
        self.assertNotEqual(cov_period, None)

        # add a funding agency element with only the required name value type
        metadata.create_element('fundingagency', agency_name='NSF')
        # there should be 1 funding agency element now
        self.assertEqual(self.composite_resource.metadata.funding_agencies.count(), 1)
        # add another identifier
        metadata.create_element('identifier', name='someIdentifier', url="http://some.org/001")
        # there should be 2 identifier elements
        self.assertEqual(self.composite_resource.metadata.identifiers.count(), 2)
        # add publisher element
        publisher_CUAHSI = "Consortium of Universities for the Advancement of " \
                           "Hydrologic Science, Inc. (CUAHSI)"
        url_CUAHSI = 'https://www.cuahsi.org'
        # publisher element can be added when the resource is published
        self.composite_resource.raccess.published = True
        self.composite_resource.raccess.save()
        # user can't set CUASHI as the publisher - when the resource has no content file
        # first delete the content file
        res_file = self.composite_resource.files.first()
        hydroshare.delete_resource_file(self.composite_resource.short_id,
                                        res_file.id,
                                        self.user)
        with self.assertRaises(Exception):
            metadata.create_element('publisher', name=publisher_CUAHSI, url=url_CUAHSI)

        metadata.create_element('publisher', name='USGS', url="http://usgs.gov")
        # there should a publisher element now
        self.assertNotEqual(self.composite_resource.metadata.publisher, None)
        # add a relation element of uri type
        metadata.create_element('relation', type='isPartOf',
                                value='http://hydroshare.org/resource/001')
        # there should be 1 relation element
        self.assertEqual(self.composite_resource.metadata.relations.count(), 1)
        # add a source element of uri type
        metadata.create_element('source', derived_from='http://hydroshare.org/resource/0001')
        # there should be 1 source element
        self.assertEqual(self.composite_resource.metadata.sources.count(), 1)
        # add 2 subject elements
        metadata.create_element('subject', value='sub-1')
        metadata.create_element('subject', value='sub-2')
        # there should be 2 subject elements
        self.assertEqual(self.composite_resource.metadata.subjects.count(), 2)
        # add key/value metadata
        self.composite_resource.extra_metadata = {'key-1': 'value-1', 'key-2': 'value-2'}
        self.composite_resource.save()
        self.assertEqual(self.composite_resource.extra_metadata,
                         {'key-1': 'value-1', 'key-2': 'value-2'})

        # test update metadata

        # test update title
        metadata.update_element('title', self.composite_resource.metadata.title.id,
                                value="New Title")
        self.assertEqual(self.composite_resource.metadata.title.value, 'New Title')
        # test update abstract
        metadata.update_element('description',
                                self.composite_resource.metadata.description.id,
                                abstract='Updated composite resource')
        self.assertEqual(self.composite_resource.metadata.description.abstract,
                         'Updated composite resource')
        # test updating funding agency
        agency_element = self.composite_resource.metadata.funding_agencies.all().filter(
            agency_name='NSF').first()
        metadata.update_element('fundingagency', agency_element.id,
                                award_title="Cyber Infrastructure",
                                award_number="NSF-101-20-6789",
                                agency_url="http://www.nsf.gov")
        agency_element = self.composite_resource.metadata.funding_agencies.all().filter(
            agency_name='NSF').first()
        self.assertEquals(agency_element.agency_name, 'NSF')
        self.assertEquals(agency_element.award_title, 'Cyber Infrastructure')
        self.assertEquals(agency_element.award_number, 'NSF-101-20-6789')
        self.assertEquals(agency_element.agency_url, 'http://www.nsf.gov')
        some_idf = self.composite_resource.metadata.identifiers.all().filter(
            name='someIdentifier').first()
        metadata.update_element('identifier', some_idf.id,  name='someOtherIdentifier')
        some_idf = self.composite_resource.metadata.identifiers.all().filter(
            name='someOtherIdentifier').first()
        self.assertNotEqual(some_idf, None)
        # update language
        self.assertEqual(self.composite_resource.metadata.language.code, 'eng')
        metadata.update_element('language',
                                self.composite_resource.metadata.language.id, code='fre')
        self.assertEqual(self.composite_resource.metadata.language.code, 'fre')
        # test that updating publisher element raises exception
        with self.assertRaises(Exception):
            metadata.update_element('publisher',
                                    self.composite_resource.metadata.publisher.id,
                                    name='USU', url="http://usu.edu")
        # test update relation type
        rel_to_update = self.composite_resource.metadata.relations.all().filter(
            type='isPartOf').first()
        metadata.update_element('relation', rel_to_update.id,
                                type='isVersionOf', value="dummy value 2")
        rel_to_update = self.composite_resource.metadata.relations.all().filter(
            type='isVersionOf').first()
        self.assertEqual(rel_to_update.value, "dummy value 2")
        src_1 = self.composite_resource.metadata.sources.all().filter(
            derived_from='http://hydroshare.org/resource/0001').first()
        metadata.update_element('source', src_1.id,
                                derived_from='http://hydroshare.org/resource/0002')
        src_1 = self.composite_resource.metadata.sources.first()
        self.assertEqual(src_1.derived_from, 'http://hydroshare.org/resource/0002')
        # change the point coverage to type box
        # even if we deleted the content file, the resource should still have the 2 coverage
        # elements
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 2)
        # delete the resource level point type coverage
        self.composite_resource.metadata.coverages.all().filter(type='point').first().delete()
        # add a point type coverage
        value_dict = {'east': '56.45678', 'north': '12.6789', 'units': 'decimal deg'}
        metadata.create_element('coverage', type='point', value=value_dict)
        value_dict = {'northlimit': '56.45678', 'eastlimit': '120.6789', 'southlimit': '16.45678',
                      'westlimit': '16.6789',
                      'units': 'decimal deg'}
        cov_pt = self.composite_resource.metadata.coverages.all().filter(type='point').first()
        metadata.update_element('coverage', cov_pt.id, type='box',  value=value_dict)
        cov_pt = self.composite_resource.metadata.coverages.all().filter(type='point').first()
        self.assertEqual(cov_pt, None)
        cov_box = self.composite_resource.metadata.coverages.all().filter(type='box').first()
        self.assertNotEqual(cov_box, None)

        # update creator
        creator = self.composite_resource.metadata.creators.all().filter(name='John Smith').first()
        self.assertEqual(creator.email, None)
        metadata.update_element('creator', creator.id, email='JSmith@gmail.com')
        creator = self.composite_resource.metadata.creators.all().filter(name='John Smith').first()
        self.assertEqual(creator.email, 'JSmith@gmail.com')
        # update contributor
        contributor = self.composite_resource.metadata.contributors.first()
        self.assertEqual(contributor.email, None)
        metadata.update_element('contributor', contributor.id, email='LSmith@gmail.com')
        contributor = self.composite_resource.metadata.contributors.first()
        self.assertEqual(contributor.email, 'LSmith@gmail.com')

    def test_delete_coverage(self):
        """Here we are testing deleting of temporal and coverage metadata for composite resource"""

        self.create_composite_resource()
        # test deleting spatial coverage
        self.assertEqual(self.composite_resource.metadata.spatial_coverage, None)
        value_dict = {'east': '56.45678', 'north': '12.6789', 'units': 'Decimal degree'}
        self.composite_resource.metadata.create_element('coverage', type='point', value=value_dict)
        self.assertNotEqual(self.composite_resource.metadata.spatial_coverage, None)
        self.composite_resource.delete_coverage(coverage_type='spatial')
        self.assertEqual(self.composite_resource.metadata.spatial_coverage, None)

        # test deleting temporal coverage
        self.assertEqual(self.composite_resource.metadata.temporal_coverage, None)
        value_dict = {'name': 'Name for period coverage', 'start': '1/1/2000', 'end': '12/12/2012'}
        self.composite_resource.metadata.create_element('coverage', type='period', value=value_dict)
        self.assertNotEqual(self.composite_resource.metadata.temporal_coverage, None)
        self.composite_resource.delete_coverage(coverage_type='temporal')
        self.assertEqual(self.composite_resource.metadata.temporal_coverage, None)

    def test_metadata_xml(self):
        """Test that the call to resource.get_metadata_xml() doesn't raise exception
        for composite resource type get_metadata_xml()
        """

        # 1. create core metadata elements
        # 2. create genericlogicalfile type metadata
        # 3. create georasterlogicalfile type metadata

        self.create_composite_resource()
        # add a file to the resource to auto create format element
        self.add_file_to_resource(file_to_add=self.generic_file)

        # add a raster file to the resource to auto create format element
        self.add_file_to_resource(file_to_add=self.raster_file)

        self.assertEqual(self.composite_resource.files.all().count(), 2)
        # add some core metadata
        # create abstract
        metadata = self.composite_resource.metadata
        metadata.create_element('description', abstract='new abstract for the resource')
        # add a contributor
        metadata.create_element('contributor', name='Lisa Smith')
        # add a funding agency element with only the required name value type
        metadata.create_element('fundingagency', agency_name='NSF')
        # add a relation element of uri type
        metadata.create_element('relation', type='isPartOf',
                                value='http://hydroshare.org/resource/001')
        # add a source element of uri type
        metadata.create_element('source', derived_from='http://hydroshare.org/resource/0001')
        # add 2 subject elements
        metadata.create_element('subject', value='sub-1')
        metadata.create_element('subject', value='sub-2')
        # add key/value metadata
        self.composite_resource.extra_metadata = {'key-1': 'value-1', 'key-2': 'value-2'}
        self.composite_resource.save()
        # add a publisher element
        self.composite_resource.raccess.published = True
        self.composite_resource.raccess.save()
        publisher_CUAHSI = "Consortium of Universities for the Advancement of " \
                           "Hydrologic Science, Inc. (CUAHSI)"
        url_CUAHSI = 'https://www.cuahsi.org'
        metadata.create_element('publisher', name=publisher_CUAHSI, url=url_CUAHSI)

        # test no exception raised when generating the metadata xml for this resource type
        try:
            self.composite_resource.get_metadata_xml()
        except Exception as ex:
            self.fail("Failed to generate metadata in xml format. Error:{}".format(ex.message))

    def test_resource_coverage_auto_update(self):
        # this is to test that the spatial coverage and temporal coverage
        # for composite resource get updated by the system based on the
        # coverage metadata that all logical file objects of the resource have at anytime

        # 1. test that resource coverages get updated on LFO level metadata creation if the
        # resource level coverage data is missing
        # 2. test that resource coverages get updated on LFO level metadata update only if the
        # update resource level coverage metadata function is called
        # 3. test that resource coverages get updated on content file delete only if the
        # update resource level coverage metadata function is called

        # create a composite resource with no content file
        self.create_composite_resource()
        typed_resource = get_resource_by_shortkey(self.composite_resource.short_id)
        # at this point the there should not be any resource level coverage metadata
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 0)
        # now add the raster tif file to the resource
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        res_file = self.composite_resource.files.all().first()
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)
        self.assertEqual(self.composite_resource.files.count(), 2)
        # raster logical file should have a coverage element of type box
        res_file = [f for f in self.composite_resource.files.all()
                    if f.logical_file_type_name == "GeoRasterLogicalFile"][0]

        raster_logical_file = res_file.logical_file
        self.assertEqual(raster_logical_file.metadata.coverages.count(), 1)
        self.assertEqual(raster_logical_file.metadata.coverages.all().filter(
            type='box').count(), 1)
        # now the resource should have a coverage metadata element of type box
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 1)
        self.assertEqual(self.composite_resource.metadata.coverages.all().filter(
            type='box').count(), 1)

        # the spatial coverage at the file type level should be exactly the same as the
        # resource level - due to auto update feature in composite resource. Note: auto update
        # occurs only if the coverage is missing at the resource level
        res_coverage = self.composite_resource.metadata.coverages.all().filter(type='box').first()
        raster_lfo_coverage = raster_logical_file.metadata.coverages.all().filter(
            type='box').first()
        self.assertEqual(res_coverage.value['projection'], raster_lfo_coverage.value['projection'])
        self.assertEqual(res_coverage.value['units'], raster_lfo_coverage.value['units'])
        self.assertEqual(res_coverage.value['northlimit'], raster_lfo_coverage.value['northlimit'])
        self.assertEqual(res_coverage.value['southlimit'], raster_lfo_coverage.value['southlimit'])
        self.assertEqual(res_coverage.value['eastlimit'], raster_lfo_coverage.value['eastlimit'])
        self.assertEqual(res_coverage.value['westlimit'], raster_lfo_coverage.value['westlimit'])

        # At this point there is not temporal coverage either at the file type level or resource
        # level
        self.assertEqual(self.composite_resource.metadata.coverages.all().filter(
            type='period').count(), 0)
        self.assertEqual(raster_logical_file.metadata.coverages.all().filter(
            type='period').count(), 0)

        # adding temporal coverage to the logical file should add the temporal coverage to the
        # resource - auto update action as the resource is missing temporal coverage data
        value_dict = {'start': '1/1/2010', 'end': '12/12/2015'}
        raster_logical_file.metadata.create_element('coverage', type='period', value=value_dict)
        self.assertEqual(self.composite_resource.metadata.coverages.all().filter(
            type='period').count(), 1)
        self.assertEqual(raster_logical_file.metadata.coverages.all().filter(
            type='period').count(), 1)
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='period').first()
        raster_lfo_coverage = raster_logical_file.metadata.coverages.all().filter(
            type='period').first()
        self.assertEqual(res_coverage.value['start'], raster_lfo_coverage.value['start'])
        self.assertEqual(res_coverage.value['end'], raster_lfo_coverage.value['end'])
        self.assertEqual(res_coverage.value['start'], '1/1/2010')
        self.assertEqual(res_coverage.value['end'], '12/12/2015')

        # test updating the temporal coverage for file type should not update the temporal coverage
        # for the resource automatically since the resource already has temporal data
        value_dict = {'start': '12/1/2010', 'end': '12/1/2015'}
        raster_logical_file.metadata.update_element('coverage', raster_lfo_coverage.id,
                                                    type='period', value=value_dict)
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='period').first()
        raster_lfo_coverage = raster_logical_file.metadata.coverages.all().filter(
            type='period').first()
        self.assertNotEqual(res_coverage.value['start'], raster_lfo_coverage.value['start'])
        self.assertNotEqual(res_coverage.value['end'], raster_lfo_coverage.value['end'])

        # test aggregation/logical file temporal coverage has changed
        self.assertEqual(raster_lfo_coverage.value['start'], '12/1/2010')
        self.assertEqual(raster_lfo_coverage.value['end'], '12/1/2015')

        # test resource temporal coverage has not changed
        self.assertEqual(res_coverage.value['start'], '1/1/2010')
        self.assertEqual(res_coverage.value['end'], '12/12/2015')

        # test updating the resource coverage by user action - which should update the resource
        # coverage as a superset of all coverages of all the contained aggregations/logical files
        typed_resource.update_temporal_coverage()
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='period').first()
        raster_lfo_coverage = raster_logical_file.metadata.coverages.all().filter(
            type='period').first()
        self.assertEqual(res_coverage.value['start'], raster_lfo_coverage.value['start'])
        self.assertEqual(res_coverage.value['end'], raster_lfo_coverage.value['end'])

        # test aggregation/logical file temporal coverage has changed
        self.assertEqual(raster_lfo_coverage.value['start'], '12/1/2010')
        self.assertEqual(raster_lfo_coverage.value['end'], '12/1/2015')

        # test that the resource coverage is superset of file type (aggregation) coverages
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 3)
        res_file = [f for f in self.composite_resource.files.all()
                    if f.extension == ".txt"][0]

        # crate a generic logical file type
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, res_file.id)

        res_file = [f for f in self.composite_resource.files.all()
                    if f.logical_file_type_name == "GenericLogicalFile"][0]

        generic_logical_file = res_file.logical_file
        # there should not be any coverage for the generic LFO at this point
        self.assertEqual(generic_logical_file.metadata.coverages.count(), 0)
        # create temporal coverage for generic LFO
        value_dict = {'start': '1/1/2009', 'end': '1/1/2015'}
        generic_logical_file.metadata.create_element('coverage', type='period', value=value_dict)
        self.assertEqual(generic_logical_file.metadata.coverages.count(), 1)
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='period').first()
        self.assertNotEqual(res_coverage, None)

        # test updating the resource coverage by user action - which should update the resource
        # coverage as a superset of all coverages of all the contained aggregations/logical files
        typed_resource.update_temporal_coverage()
        typed_resource.update_spatial_coverage()
        # resource temporal coverage is now super set of the 2 temporal coverages
        # in 2 LFOs
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='period').first()
        self.assertEqual(res_coverage.value['start'], '1/1/2009')
        self.assertEqual(res_coverage.value['end'], '12/1/2015')
        # test resource superset spatial coverage
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='box').first()
        self.assertEqual(res_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(res_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(res_coverage.value['northlimit'], 42.0500269597691)
        self.assertEqual(res_coverage.value['eastlimit'], -111.57773718106195)
        self.assertEqual(res_coverage.value['southlimit'], 41.98722286029891)
        self.assertEqual(res_coverage.value['westlimit'], -111.69756293084055)
        value_dict = {'east': '-110.88845678', 'north': '43.6789', 'units': 'Decimal deg'}
        generic_logical_file.metadata.create_element('coverage', type='point', value=value_dict)

        # update resource spatial coverage from aggregations spatial coverages
        typed_resource.update_spatial_coverage()
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='box').first()
        self.assertEqual(res_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(res_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(res_coverage.value['northlimit'], 43.6789)
        self.assertEqual(res_coverage.value['eastlimit'], -110.88845678)
        self.assertEqual(res_coverage.value['southlimit'], 41.98722286029891)
        self.assertEqual(res_coverage.value['westlimit'], -111.69756293084055)
        # update the LFO coverage to box type
        value_dict = {'eastlimit': '-110.88845678', 'northlimit': '43.6789',
                      'westlimit': '-112.78967', 'southlimit': '40.12345',
                      'units': 'Decimal deg'}
        lfo_spatial_coverage = generic_logical_file.metadata.spatial_coverage
        generic_logical_file.metadata.update_element('coverage', lfo_spatial_coverage.id,
                                                     type='box', value=value_dict)

        # update resource spatial coverage from aggregations spatial coverages
        typed_resource.update_spatial_coverage()

        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='box').first()
        self.assertEqual(res_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(res_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(res_coverage.value['northlimit'], 43.6789)
        self.assertEqual(res_coverage.value['eastlimit'], -110.88845678)
        self.assertEqual(res_coverage.value['southlimit'], 40.12345)
        self.assertEqual(res_coverage.value['westlimit'], -112.78967)

        # deleting the generic file (aggregation) should NOT reset the coverage of the resource to
        # that of the raster LFO (aggregation)
        res_file = [f for f in self.composite_resource.files.all()
                    if f.logical_file_type_name == "GenericLogicalFile"][0]
        hydroshare.delete_resource_file(self.composite_resource.short_id, res_file.id, self.user)
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='box').first()
        raster_lfo_coverage = raster_logical_file.metadata.coverages.all().filter(
            type='box').first()
        self.assertEqual(res_coverage.value['projection'], raster_lfo_coverage.value['projection'])
        self.assertEqual(res_coverage.value['units'], raster_lfo_coverage.value['units'])
        self.assertNotEqual(res_coverage.value['northlimit'],
                            raster_lfo_coverage.value['northlimit'])
        self.assertNotEqual(res_coverage.value['southlimit'],
                            raster_lfo_coverage.value['southlimit'])
        self.assertNotEqual(res_coverage.value['eastlimit'], raster_lfo_coverage.value['eastlimit'])
        self.assertNotEqual(res_coverage.value['westlimit'], raster_lfo_coverage.value['westlimit'])
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='period').first()
        raster_lfo_coverage = raster_logical_file.metadata.coverages.all().filter(
            type='period').first()
        self.assertNotEqual(res_coverage.value['start'], raster_lfo_coverage.value['start'])
        self.assertEqual(res_coverage.value['end'], raster_lfo_coverage.value['end'])
        self.assertNotEqual(res_coverage.value['start'], '12/1/2010')
        self.assertEqual(res_coverage.value['end'], '12/1/2015')

        # deleting the remaining content file from resource should leave the resource
        # coverage element unchanged
        res_file = [f for f in self.composite_resource.files.all()
                    if f.logical_file_type_name == "GeoRasterLogicalFile"][0]
        hydroshare.delete_resource_file(self.composite_resource.short_id, res_file.id, self.user)
        self.assertEqual(self.composite_resource.files.count(), 0)
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 2)

    def test_get_aggregations(self):
        """Here wre are testing the function 'get_logical_files()'
        Test for single file aggregation and multi-file aggregation (logical file)
        """

        self.create_composite_resource()

        # at this point resource can't be public or discoverable as some core metadata missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        self.assertEqual(len(self.composite_resource.get_logical_files('GenericLogicalFile')), 0)
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # now create a generic aggregation - single-file aggregation
        gen_res_file = self.composite_resource.files.first()
        # crate a generic logical file type
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, gen_res_file.id)
        self.assertEqual(len(self.composite_resource.get_logical_files('GenericLogicalFile')), 1)
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        self.assertEqual(len(self.composite_resource.get_logical_files('GeoRasterLogicalFile')), 0)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)

        # add a tif file
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 2)
        # make the tif as part of the GeoRasterLogicalFile - multi-file aggregation
        tif_res_file = [f for f in self.composite_resource.files.all()
                        if f.extension == ".tif"][0]
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, tif_res_file.id)

        self.assertEqual(len(self.composite_resource.get_logical_files('GeoRasterLogicalFile')), 1)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)

        self.assertEqual(len(self.composite_resource.get_logical_files('GenericLogicalFile')), 1)
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

    def test_can_be_public_or_discoverable_with_no_aggregation(self):
        """Here we are testing the function 'can_be_public_or_discoverable()'
        This function should return False unless we have the required metadata at the resource level
        when the resource contains no aggregation (logical file)
        """

        self.create_composite_resource()

        # at this point resource can't be public or discoverable as some core metadata missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)

        # at this point still resource can't be public or discoverable - as some core metadata
        # is missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)

        # there should be 3 required core metadata elements missing at this point
        missing_elements = self.composite_resource.metadata.get_required_missing_elements()
        self.assertEqual(len(missing_elements), 2)
        self.assertIn('Abstract', missing_elements)
        self.assertIn('Keywords', missing_elements)

        # add the above missing elements
        # create abstract
        metadata = self.composite_resource.metadata
        # add Abstract (element name is description)
        metadata.create_element('description', abstract='new abstract for the resource')
        # add keywords (element name is subject)
        metadata.create_element('subject', value='sub-1')
        # at this point resource can be public or discoverable
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, True)

    def test_cannot_be_published_with_refenced_url_single_file_aggregation(self):
        """
        test a composite resource that includes referenced url single file aggregation cannot be
        published
        """
        self.create_composite_resource()
        url_file_base_name = 'test_url'
        ret_status, msg, _ = add_reference_url_to_resource(self.user,
                                                           self.composite_resource.short_id,
                                                           self.valid_url, url_file_base_name,
                                                           'data/contents')
        self.assertEqual(ret_status, status.HTTP_200_OK)
        # at this point resource can't be public or discoverable as some core metadata missing
        self.assertFalse(self.composite_resource.can_be_public_or_discoverable)
        missing_elements = self.composite_resource.metadata.get_required_missing_elements()
        self.assertEqual(len(missing_elements), 2)
        self.assertIn('Abstract', missing_elements)
        self.assertIn('Keywords', missing_elements)
        # add the above missing elements
        # create abstract
        metadata = self.composite_resource.metadata
        # add Abstract (element name is description)
        metadata.create_element('description', abstract='new abstract for the resource')
        # add keywords (element name is subject)
        metadata.create_element('subject', value='sub-1')
        # at this point resource can be public or discoverable, but cannot be published
        self.assertTrue(self.composite_resource.can_be_public_or_discoverable)
        self.assertFalse(self.composite_resource.can_be_published)

    def test_can_be_public_or_discoverable_with_single_file_aggregation(self):
        """Here we are testing the function 'can_be_public_or_discoverable()'
        This function should return False unless we have the required metadata at the resource level
        when the resource contains a single file aggregation (e.g., generic aggregation).
        """

        self.create_composite_resource()

        # at this point resource can't be public or discoverable as some core metadata missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)

        gen_res_file = self.composite_resource.files.first()
        # crate a generic logical file type
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, gen_res_file.id)

        # at this point still resource can't be public or discoverable - as some core metadata
        # is missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)

        # there should be 3 required core metadata elements missing at this point
        missing_elements = self.composite_resource.metadata.get_required_missing_elements()
        self.assertEqual(len(missing_elements), 2)
        self.assertIn('Abstract', missing_elements)
        self.assertIn('Keywords', missing_elements)

        # add the above missing elements
        # create abstract
        metadata = self.composite_resource.metadata
        # add Abstract (element name is description)
        metadata.create_element('description', abstract='new abstract for the resource')
        # add keywords (element name is subject)
        metadata.create_element('subject', value='sub-1')
        # at this point resource can be public or discoverable
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, True)

    def test_can_be_public_or_discoverable_with_multi_file_aggregation(self):
        """Here we are testing the function 'can_be_public_or_discoverable()'
        This function should return False unless we have the required metadata at the resource level
        when the resource contains a multi-file aggregation (e.g., raster aggregation)
        """

        self.create_composite_resource()

        # at this point resource can't be public or discoverable as some core metadata missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)
        # add a tif file
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = self.composite_resource.files.first()
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, tif_res_file.id)

        # at this point still resource can't be public or discoverable - as some core metadata
        # is missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)

        # there should be 3 required core metadata elements missing at this point
        missing_elements = self.composite_resource.metadata.get_required_missing_elements()
        self.assertEqual(len(missing_elements), 2)
        self.assertIn('Abstract', missing_elements)
        self.assertIn('Keywords', missing_elements)

        # add the above missing elements
        # create abstract
        metadata = self.composite_resource.metadata
        # add Abstract (element name is description)
        metadata.create_element('description', abstract='new abstract for the resource')
        # add keywords (element name is subject)
        metadata.create_element('subject', value='sub-1')
        # at this point resource can be public or discoverable
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, True)

    def test_supports_folder_creation_non_aggregation_folder(self):
        """Here we are testing the function supports_folder_creation()
        Test that this function returns True when we check for creating a folder inside a folder
        that contains a resource file that is not part of any aggregation
        """

        self.create_composite_resource()
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        gen_res_file = self.composite_resource.files.first()
        self.assertEqual(gen_res_file.file_folder, None)
        # we should be able to create this new folder
        new_folder_full_path = os.path.join(self.composite_resource.file_path, "my-new-folder")
        self.assertEqual(self.composite_resource.supports_folder_creation(new_folder_full_path),
                         True)
        # create the folder
        new_folder_path = os.path.join("data", "contents", "my-new-folder")
        create_folder(self.composite_resource.short_id, new_folder_path)
        old_file_path = self.composite_resource.files.get().short_path
        # now move the file to this new folder
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      os.path.join("data", "contents", old_file_path),
                                      os.path.join(new_folder_path, self.generic_file_name))

        gen_res_file = self.composite_resource.files.first()
        self.assertEqual(gen_res_file.file_folder, 'my-new-folder')
        # test that we should be able to create a folder inside the folder that contains
        # a resource file that is part of a Generic Logical file
        new_folder_full_path = os.path.join(new_folder_full_path, "another-folder")
        self.assertTrue(self.composite_resource.supports_folder_creation(new_folder_full_path))

    def test_supports_folder_creation_single_file_aggregation_folder(self):
        """Here we are testing the function supports_folder_creation()
        Test that this function returns True when we check for creating a folder inside a folder
        that contains a single-file aggregation (e.g., generic aggregation)
        """
        self.create_composite_resource()
        # add a file to the resource which will be part of  a GenericLogicalFile object
        self.add_file_to_resource(file_to_add=self.generic_file)

        self.assertEqual(self.composite_resource.files.count(), 1)
        gen_res_file = self.composite_resource.files.first()
        # crate a generic logical file type
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, gen_res_file.id)
        # we should be able to create this new folder
        new_folder = "my-new-folder"
        new_folder_full_path = os.path.join(self.composite_resource.file_path, new_folder)
        self.assertEqual(self.composite_resource.supports_folder_creation(new_folder_full_path),
                         True)
        # create the folder
        new_folder_path = os.path.join("data", "contents", new_folder)
        create_folder(self.composite_resource.short_id, new_folder_path)
        old_file_path = self.composite_resource.files.get().short_path
        # now move the file to this new folder
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      os.path.join("data", "contents", old_file_path),
                                      os.path.join(new_folder_path, self.generic_file_name))

        # test that we should be able to create a folder inside the folder that contains
        # a resource file that is part of a Generic Logical file
        new_folder_full_path = os.path.join(new_folder_full_path, "another-folder")
        self.assertTrue(self.composite_resource.supports_folder_creation(new_folder_full_path))

    def test_supports_folder_creation_multi_file_aggregation_folder(self):
        """Here we are testing the function supports_folder_creation()
        Test that this function returns False when we check for creating a folder inside a folder
        that represents a multi-file aggregation (e.g., raster aggregation)
        """
        self.create_composite_resource()

        # add a raster tif file to the resource which will be part of
        # a GoeRasterLogicalFile object
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = self.composite_resource.files.first()
        self.assertEqual(tif_res_file.file_folder, None)
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, tif_res_file.id)
        tif_res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(tif_res_file.file_name)
        expected_folder = base_file_name
        self.assertEqual(tif_res_file.file_folder, expected_folder)
        self.assertEqual(tif_res_file.file_name, self.raster_file_name)

        # test that creating a folder at aggregation folder is not supported
        # as that folder represetns a multi-file aggregation (raster aggregation)
        new_folder_path = os.path.join(self.composite_resource.file_path,
                                       tif_res_file.file_folder, 'my-new-folder')
        self.assertEqual(self.composite_resource.supports_folder_creation(new_folder_path), False)

    def test_supports_rename_single_file_aggregation_file(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class
        Test that it should be possible to rename a file that is part of a single-file aggregation
        (e.g., generic aggregation)
        """

        self.create_composite_resource()
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)

        self.assertEqual(self.composite_resource.files.count(), 1)
        # test that we can rename the resource file that's part of the GenericLogical File
        gen_res_file = self.composite_resource.files.first()
        # crate a generic logical file type
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, gen_res_file.id)
        self.assertEqual(self.generic_file_name, gen_res_file.file_name)
        # rename file
        file_rename = 'renamed_file.txt'
        self.assertNotEqual(gen_res_file.file_name, file_rename)
        src_full_path = os.path.join(self.composite_resource.file_path, self.generic_file_name)
        tgt_full_path = os.path.join(self.composite_resource.file_path, file_rename)
        # this is the function we are testing
        self.assertEqual(self.composite_resource.supports_rename_path(
            src_full_path, tgt_full_path), True)

    def test_supports_rename_multi_file_aggregation_file(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class
        Test that it shouldn't be possible to rename a file that is part of a multi-file
        aggregation (e.g., raster aggregation)
        """

        self.create_composite_resource()

        # add a raster tif file to the resource which will be part of
        # a GoeRasterLogicalFile object
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = self.composite_resource.files.first()
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, tif_res_file.id)
        tif_res_file = self.composite_resource.files.first()
        # test renaming of any files that are part of GeoRasterLogicalFile is not allowed
        file_rename = 'small_logan_1.tif'
        self.assertNotEqual(tif_res_file.file_name, file_rename)
        src_full_path = os.path.join(self.composite_resource.file_path,
                                     tif_res_file.file_folder, self.raster_file_name)
        tgt_full_path = os.path.join(self.composite_resource.file_path,
                                     tif_res_file.file_folder, file_rename)

        # this is the function we are testing
        self.assertEqual(self.composite_resource.supports_rename_path(
            src_full_path, tgt_full_path), False)

    def test_supports_move_single_file_aggregation_file(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class
        Test that it should be possible to move a single file aggregation
        (e.g., generic aggregation) to a folder that doesn't represent an aggregation
        """

        self.create_composite_resource()
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)

        self.assertEqual(self.composite_resource.files.count(), 1)
        # test that we can rename the resource file that's part of the GenericLogical File
        gen_res_file = self.composite_resource.files.first()
        # crate a generic logical file type - single file aggregation
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, gen_res_file.id)
        src_full_path = os.path.join(self.composite_resource.file_path, self.generic_file_name)

        # create a new folder so that we can test if the generic file can be moved there or not
        new_folder = "my-new-folder"
        new_folder_full_path = os.path.join(self.composite_resource.file_path, new_folder)
        new_folder_path = os.path.join("data", "contents", new_folder)
        self.assertTrue(self.composite_resource.supports_folder_creation(new_folder_full_path))
        # create the folder
        create_folder(self.composite_resource.short_id, new_folder_path)
        # set the target path for the file to be moved to
        tgt_full_path = os.path.join(new_folder_full_path, self.generic_file_name)
        # this is the function we are testing
        self.assertEqual(self.composite_resource.supports_rename_path(
            src_full_path, tgt_full_path), True)

    def test_supports_rename_single_file_aggregation_folder(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class
        Test that it should be possible to rename a folder that contains a single file aggregation
        (e.g., generic aggregation)
        """

        self.create_composite_resource()
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)

        self.assertEqual(self.composite_resource.files.count(), 1)
        # test that we can rename the resource file that's part of the GenericLogical File
        gen_res_file = self.composite_resource.files.first()
        # crate a generic logical file type
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, gen_res_file.id)
        gen_res_file_basename = hydroshare.utils.get_resource_file_name_and_extension(
            gen_res_file)[1]
        self.assertEqual(self.generic_file_name, gen_res_file_basename)

        # create a new folder and move the generic aggregation file there
        new_folder = "my-new-folder"
        new_folder_path = os.path.join("data", "contents", new_folder)
        create_folder(self.composite_resource.short_id, new_folder_path)
        src_path = os.path.join('data', 'contents', self.generic_file_name)
        tgt_path = new_folder_path
        # now move the file to this new folder
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        # test rename folder
        folder_rename = '{}-1'.format(new_folder)
        src_full_path = os.path.join(self.composite_resource.file_path, new_folder)
        tgt_full_path = os.path.join(self.composite_resource.file_path, folder_rename)
        # this is the function we are testing
        self.assertEqual(self.composite_resource.supports_rename_path(
            src_full_path, tgt_full_path), True)

    def test_supports_rename_multi_file_aggregation_folder(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class
        Test that it should be possible to rename a folder that contains a multi-file aggregation
        (e.g., raster aggregation)
        """

        self.create_composite_resource()
        # add a raster tif file to the resource which will be part of
        # a GoeRasterLogicalFile object
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = self.composite_resource.files.first()
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, tif_res_file.id)
        res_file = self.composite_resource.files.first()
        self.assertNotEqual(res_file.file_folder, None)

        # test renaming a folder that contains resource files that are part of the
        # GeoRasterLogicalFile is allowed
        folder_rename = '{}_1'.format(res_file.file_folder)
        src_full_path = os.path.join(self.composite_resource.file_path,  res_file.file_folder)
        tgt_full_path = os.path.join(self.composite_resource.file_path,  folder_rename)
        # this is the function we are testing
        self.assertEqual(self.composite_resource.supports_rename_path(
            src_full_path, tgt_full_path), True)

    def test_supports_move_multi_file_aggregation_file(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class
        Test that it should not be possible to move a file that is part of a multi-file aggregation
        (e.g., raster aggregation)
        """

        self.create_composite_resource()

        # add a raster tif file to the resource which will be part of
        # a GoeRasterLogicalFile object
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = self.composite_resource.files.first()
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, tif_res_file.id)

        # create a new folder where to move the multi-file aggregation file - the tif file
        new_folder = "my-new-folder"
        new_folder_path = os.path.join("data", "contents", new_folder)
        create_folder(self.composite_resource.short_id, new_folder_path)
        # test that we can't  move a file to a folder that contains resource files that are part
        # of GeoRasterLogicalFile object
        tif_res_file = self.composite_resource.files.first()
        src_full_path = tif_res_file.storage_path
        tgt_full_path = os.path.join(self.composite_resource.file_path, new_folder)
        # this is the function we are testing
        self.assertEqual(self.composite_resource.supports_rename_path(
            src_full_path, tgt_full_path), False)

    def test_supports_move_multi_file_aggregation_folder(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class
        Test that it should be possible to move a folder that represents a multi-file aggregation
        (e.g., raster aggregation) to a folder that does not represent any multi-file aggregation
        """

        self.create_composite_resource()

        # add a raster tif file to the resource which will be part of
        # a GoeRasterLogicalFile object
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = self.composite_resource.files.first()
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, tif_res_file.id)
        res_file = self.composite_resource.files.first()
        self.assertNotEqual(res_file.file_folder, None)

        # create a new folder
        new_folder = '{}_1'.format(res_file.file_folder)
        new_folder_path = os.path.join("data", "contents", new_folder)
        create_folder(self.composite_resource.short_id, new_folder_path)

        # test it should be possible to move the 'small_logan' folder that
        # represents the raster aggregation to the 'my-new-folder' that we created above
        src_full_path = os.path.join(self.composite_resource.file_path, res_file.file_folder)
        tgt_full_path = os.path.join(self.composite_resource.file_path, new_folder)
        # this is the function we are testing
        self.assertEqual(self.composite_resource.supports_rename_path(
            src_full_path, tgt_full_path), True)

    def test_supports_zip_non_aggregation_folder(self):
        """Here we are testing the function supports_zip()
        Test that zipping a folder that contains file(s) that is not part of any aggregation
        is allowed
        """

        self.create_composite_resource()

        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        new_folder = 'my-new-folder'
        new_folder_path = "data/contents/{}".format(new_folder)

        # create a new folder
        create_folder(self.composite_resource.short_id, new_folder_path)
        # now move the file to this new folder
        src_path = os.path.join('data', 'contents', self.generic_file_name)
        tgt_path = os.path.join(new_folder_path, self.generic_file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        # test that we can zip the folder my_new_folder as this folder has no aggregation
        folder_to_zip = os.path.join(self.composite_resource.file_path, new_folder)
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), True)

    def test_supports_zip_single_file_aggregation_folder(self):
        """Here we are testing the function supports_zip()
        Test that zipping a folder that contains a single file aggregation
        (e.g., generic aggregation) is not allowed
        """

        self.create_composite_resource()

        # add a file to the resource which will be part of  a GenericLogicalFile object later
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        new_folder = 'my-new-folder'
        new_folder_path = "data/contents/{}".format(new_folder)

        # create a folder
        create_folder(self.composite_resource.short_id, new_folder_path)
        # now move the file to this new folder
        src_path = os.path.join('data', 'contents', self.generic_file_name)
        tgt_path = os.path.join(new_folder_path, self.generic_file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        gen_res_file = self.composite_resource.files.first()
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, gen_res_file.id)
        # test that we can't zip the folder my_new_folder as this folder has aggregation
        folder_to_zip = os.path.join(self.composite_resource.file_path, new_folder)
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), False)

    def test_supports_zip_single_file_aggregation_parent_folder(self):
        """Here we are testing the function supports_zip()
        Test that zipping a parent folder of a folder that contains a single file aggregation
        (e.g., generic aggregation) is not allowed
        """

        self.create_composite_resource()

        # add a file to the resource which will be part of  a GenericLogicalFile object later
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        new_folder = 'generic-folder'
        new_folder_path = "data/contents/{}".format(new_folder)

        # create a folder
        create_folder(self.composite_resource.short_id, new_folder_path)
        # now move the file to this new folder
        src_path = os.path.join('data', 'contents', self.generic_file_name)
        tgt_path = os.path.join(new_folder_path, self.generic_file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        gen_res_file = self.composite_resource.files.first()
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, gen_res_file.id)

        # create a folder
        parent_folder = 'parent-folder'
        new_folder_path = "data/contents/{}".format(parent_folder)
        create_folder(self.composite_resource.short_id, new_folder_path)
        # now move the generic-folder to this new folder
        gen_res_file = self.composite_resource.files.first()
        src_path = os.path.join('data', 'contents', gen_res_file.file_folder)
        tgt_path = os.path.join(new_folder_path, gen_res_file.file_folder)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        gen_res_file = self.composite_resource.files.first()
        self.assertEqual(gen_res_file.file_folder, '{0}/{1}'.format(parent_folder, new_folder))
        # test that we can't zip the folder parent_folder as this folder contains a
        # folder (generic-folder) that has an aggregation
        folder_to_zip = os.path.join(self.composite_resource.file_path, parent_folder)
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), False)

    def test_supports_zip_multi_file_aggregation_folder(self):
        """Here we are testing the function supports_zip()
        Test that zipping a folder that represents a multi-file aggregation
        (e.g., raster aggregation) is not allowed
        """

        self.create_composite_resource()

        # add a tif file to the resource
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = self.composite_resource.files.first()
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, tif_res_file.id)
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(self.raster_file_name)
        expected_folder_name = base_file_name
        # resource file exists in a new folder
        self.assertEqual(res_file.file_folder, expected_folder_name)

        # test that we can't zip the folder that represents the aggregation
        folder_to_zip = os.path.join(self.composite_resource.file_path, res_file.file_folder)
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), False)

    def test_supports_zip_multi_file_aggregation_parent_folder(self):
        """Here we are testing the function supports_zip()
        Test that zipping a parent folder of a folder that contains a multi file aggregation
        (e.g., raster aggregation) is not allowed
        """

        self.create_composite_resource()

        # add a file to the resource which will be part of  a raster aggregation later
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 1)

        tif_res_file = self.composite_resource.files.first()
        self.assertEqual(tif_res_file.file_folder, None)
        # create the raster aggregation
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, tif_res_file.id)
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(self.raster_file_name)
        expected_folder_name = base_file_name
        self.assertEqual(res_file.file_folder, expected_folder_name)

        # create a folder
        parent_folder = 'parent-folder'
        new_folder_path = "data/contents/{}".format(parent_folder)
        create_folder(self.composite_resource.short_id, new_folder_path)
        # now move the aggregation folder to this new folder
        src_path = os.path.join('data', 'contents', res_file.file_folder)
        tgt_path = os.path.join(new_folder_path, res_file.file_folder)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)

        tif_res_file = self.composite_resource.files.first()
        self.assertEqual(tif_res_file.file_folder, '{0}/{1}'.format(parent_folder,
                                                                    res_file.file_folder))
        # test that we can't zip the folder parent_folder as this folder contains a
        # the folder that represents an aggregation
        folder_to_zip = os.path.join(self.composite_resource.file_path, parent_folder)
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), False)

    def test_supports_delete_original_folder_on_zip(self):
        """Here we are testing the function supports_delete_original_folder_on_zip() of the
        composite resource class"""

        self.create_composite_resource()

        # test that a folder containing a resource file that's part of the GenericLogicalFile
        # can be deleted after that folder gets zipped
        # add a file to the resource which will be part of  a GenericLogicalFile object
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        new_folder = 'my-new-folder'
        new_folder_path = "data/contents/{}".format(new_folder)
        # create the folder
        create_folder(self.composite_resource.short_id, new_folder_path)
        # now move the file to this new folder
        src_path = 'data/contents/{}'.format(self.generic_file_name)
        tgt_path = os.path.join(new_folder_path, self.generic_file_name)
        move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                      src_path, tgt_path)
        # folder_to_zip = self.composite_resource.short_id + '/data/contents/my-new-folder'
        folder_to_zip = os.path.join(self.composite_resource.file_path, new_folder)
        # test that we can zip the folder my_new_folder
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), True)
        # this is the function we are testing - my-new-folder can be deleted
        self.assertEqual(self.composite_resource.supports_delete_folder_on_zip(
            folder_to_zip), True)

        # test that a folder containing a resource file that's part of the GeoRasterLogicalFile
        # can't be deleted after that folder gets zipped

        # add a file to the resource which will be part of  a GeoRasterLogicalFile object
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 2)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.tif')[0]
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, tif_res_file.id)
        self.assertEqual(self.composite_resource.files.count(), 3)
        tif_res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.tif')[0]

        # resource file exists in a new folder
        base_file_name, _ = os.path.splitext(self.raster_file_name)
        expected_folder_name = base_file_name
        self.assertEqual(tif_res_file.file_folder, expected_folder_name)
        folder_to_zip = os.path.join(self.composite_resource.file_path, tif_res_file.file_folder)
        # test that we can't zip the folder my_new_folder
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), False)
        # this is the function we are testing - aggregation folder can't be deleted
        self.assertEqual(self.composite_resource.supports_delete_folder_on_zip(
            folder_to_zip), False)

    def test_copy_resource_with_no_aggregation(self):
        """Here we are testing that we can create a copy of a composite resource that contains no
        aggregations"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(self.composite_resource.short_id,
                                                                  self.user,
                                                                  action='copy')
        new_composite_resource = hydroshare.copy_resource(self.composite_resource,
                                                          new_composite_resource)
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(self.composite_resource.metadata.title.value,
                         new_composite_resource.metadata.title.value)
        self.assertEqual(self.composite_resource.files.count(),
                         new_composite_resource.files.count())
        self.assertEqual(new_composite_resource.files.count(), 1)

    def test_copy_resource_with_single_file_aggregation(self):
        """Here we are testing that we can create a copy of a composite resource that contains one
        single file aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        gen_res_file = self.composite_resource.files.first()
        # set the generic file to single file aggregation
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, gen_res_file.id)
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(self.composite_resource.short_id,
                                                                  self.user,
                                                                  action='copy')
        new_composite_resource = hydroshare.copy_resource(self.composite_resource,
                                                          new_composite_resource)
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(self.composite_resource.metadata.title.value,
                         new_composite_resource.metadata.title.value)
        self.assertEqual(self.composite_resource.files.count(),
                         new_composite_resource.files.count())
        self.assertEqual(new_composite_resource.files.count(), 1)
        self.assertEqual(GenericLogicalFile.objects.count(), 2)

    def test_copy_resource_with_file_set_aggregation_1(self):
        """Here we are testing that we can create a copy of a composite resource that contains one
        file set aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user, folder_path=new_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(self.composite_resource.short_id,
                                                                  self.user,
                                                                  action='copy')
        new_composite_resource = hydroshare.copy_resource(self.composite_resource,
                                                          new_composite_resource)
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(self.composite_resource.metadata.title.value,
                         new_composite_resource.metadata.title.value)
        self.assertEqual(self.composite_resource.files.count(),
                         new_composite_resource.files.count())
        self.assertEqual(new_composite_resource.files.count(), 1)
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)

    def test_copy_resource_with_file_set_aggregation_2(self):
        """Here we are testing that we can create a copy of a composite resource that contains one
        file set aggregation that contains another aggregation (NetCDF aggregation)"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        new_folder = 'fileset_folder'
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=new_folder)
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user, folder_path=new_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        # add the the nc file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.netcdf_file, upload_folder=new_folder)
        nc_res_file = ResourceFile.get(self.composite_resource, file=self.netcdf_file_name,
                                       folder=new_folder)
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, file_id=nc_res_file.id)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(self.composite_resource.short_id,
                                                                  self.user,
                                                                  action='copy')
        new_composite_resource = hydroshare.copy_resource(self.composite_resource,
                                                          new_composite_resource)
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(self.composite_resource.metadata.title.value,
                         new_composite_resource.metadata.title.value)
        self.assertEqual(self.composite_resource.files.count(),
                         new_composite_resource.files.count())
        # there should be 3 files - 2 files that we uploaded and one text file generated for netcdf
        # aggregation
        self.assertEqual(new_composite_resource.files.count(), 3)
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 2)

    def test_copy_resource_with_file_set_aggregation_3(self):
        """Here we are testing that we can create a copy of a composite resource that contains one
        nested file set aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        parent_fs_folder = 'parent_fs_folder'
        ResourceFile.create_folder(self.composite_resource, parent_fs_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=parent_fs_folder)
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=parent_fs_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        child_fs_folder = '{}/child_fs_folder'.format(parent_fs_folder)
        ResourceFile.create_folder(self.composite_resource, child_fs_folder)
        # add the the txt file to the resource at the above child folder
        self.add_file_to_resource(file_to_add=self.generic_file, upload_folder=child_fs_folder)
        # set the child folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(self.composite_resource, self.user,
                                         folder_path=child_fs_folder)
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(self.composite_resource.short_id,
                                                                  self.user,
                                                                  action='copy')
        new_composite_resource = hydroshare.copy_resource(self.composite_resource,
                                                          new_composite_resource)
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(self.composite_resource.metadata.title.value,
                         new_composite_resource.metadata.title.value)
        self.assertEqual(self.composite_resource.files.count(),
                         new_composite_resource.files.count())
        self.assertEqual(new_composite_resource.files.count(), 2)
        self.assertEqual(FileSetLogicalFile.objects.count(), 4)

    def test_copy_resource_with_netcdf_aggregation(self):
        """Here were testing that we can create a copy of a composite resource that contains a
        netcdf aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a nc file to the resource
        self.add_file_to_resource(file_to_add=self.netcdf_file)
        nc_res_file = self.composite_resource.files.first()
        # set the nc file to netcdf aggregation
        NetCDFLogicalFile.set_file_type(self.composite_resource, self.user, nc_res_file.id)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(self.composite_resource.short_id,
                                                                  self.user,
                                                                  action='copy')
        new_composite_resource = hydroshare.copy_resource(self.composite_resource,
                                                          new_composite_resource)
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(self.composite_resource.metadata.title.value,
                         new_composite_resource.metadata.title.value)
        self.assertEqual(self.composite_resource.files.count(),
                         new_composite_resource.files.count())
        self.assertEqual(new_composite_resource.files.count(), 2)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 2)

    def test_copy_resource_with_timeseries_aggregation(self):
        """Here were testing that we can create a copy of a composite resource that contains a
        timeseries aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a sqlite file to the resource
        self.add_file_to_resource(file_to_add=self.sqlite_file)
        sql_res_file = self.composite_resource.files.first()
        # set the sqlite file to timeseries aggregation
        TimeSeriesLogicalFile.set_file_type(self.composite_resource, self.user, sql_res_file.id)
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(self.composite_resource.short_id,
                                                                  self.user,
                                                                  action='copy')
        new_composite_resource = hydroshare.copy_resource(self.composite_resource,
                                                          new_composite_resource)
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(self.composite_resource.metadata.title.value,
                         new_composite_resource.metadata.title.value)
        self.assertEqual(self.composite_resource.files.count(),
                         new_composite_resource.files.count())
        self.assertEqual(new_composite_resource.files.count(), 1)
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 2)

    def test_copy_resource_with_reftimeseries_aggregation(self):
        """Here were testing that we can create a copy of a composite resource that contains a
        ref timeseries aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a json file to the resource
        self.add_file_to_resource(file_to_add=self.json_file)
        json_res_file = self.composite_resource.files.first()
        # set the json file to ref timeseries aggregation
        RefTimeseriesLogicalFile.set_file_type(self.composite_resource, self.user, json_res_file.id)
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(self.composite_resource.short_id,
                                                                  self.user,
                                                                  action='copy')
        new_composite_resource = hydroshare.copy_resource(self.composite_resource,
                                                          new_composite_resource)
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(self.composite_resource.metadata.title.value,
                         new_composite_resource.metadata.title.value)
        self.assertEqual(self.composite_resource.files.count(),
                         new_composite_resource.files.count())
        self.assertEqual(new_composite_resource.files.count(), 1)
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 2)

    def test_copy_resource_with_raster_aggregation(self):
        """Here were testing that we can create a copy of a composite resource that contains a
        raster aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a tif file to the resource
        self.add_file_to_resource(file_to_add=self.raster_file)
        tif_res_file = self.composite_resource.files.first()
        # set the tif file to raster aggregation
        GeoRasterLogicalFile.set_file_type(self.composite_resource, self.user, tif_res_file.id)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(self.composite_resource.short_id,
                                                                  self.user,
                                                                  action='copy')
        new_composite_resource = hydroshare.copy_resource(self.composite_resource,
                                                          new_composite_resource)
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(self.composite_resource.metadata.title.value,
                         new_composite_resource.metadata.title.value)
        self.assertEqual(self.composite_resource.files.count(),
                         new_composite_resource.files.count())
        self.assertEqual(new_composite_resource.files.count(), 2)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 2)

    def test_copy_resource_with_feature_aggregation(self):
        """Here were testing that we can create a copy of a composite resource that contains a
        geo feature aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a shp file to the resource
        self.add_file_to_resource(file_to_add=self.watershed_shp_file)
        shp_res_file = self.composite_resource.files.first()
        # add a shx file to the resource
        self.add_file_to_resource(file_to_add=self.watershed_shx_file)
        # add a dbf file to the resource
        self.add_file_to_resource(file_to_add=self.watershed_dbf_file)

        # set the shp file to raster aggregation
        GeoFeatureLogicalFile.set_file_type(self.composite_resource, self.user, shp_res_file.id)
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(self.composite_resource.short_id,
                                                                  self.user,
                                                                  action='copy')
        new_composite_resource = hydroshare.copy_resource(self.composite_resource,
                                                          new_composite_resource)
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(self.composite_resource.metadata.title.value,
                         new_composite_resource.metadata.title.value)
        self.assertEqual(self.composite_resource.files.count(),
                         new_composite_resource.files.count())
        self.assertEqual(new_composite_resource.files.count(), 3)
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 2)

    def test_unzip(self):
        """Test that when a zip file gets unzipped at data/contents/ where a single file aggregation
        exists, the single file aggregation related xml files do not get added to the resource as
        resource files """

        self.create_composite_resource()

        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        gen_res_file = self.composite_resource.files.first()
        # set the generic file to generic single file aggregation
        GenericLogicalFile.set_file_type(self.composite_resource, self.user, gen_res_file.id)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # add a zip file that contains only one file
        self.add_file_to_resource(file_to_add=self.zip_file)
        # resource should have 2 files now
        self.assertEqual(self.composite_resource.files.count(), 2)
        # unzip the above zip file  which should add one more file to the resource
        zip_res_file = ResourceFile.get(self.composite_resource, self.zip_file_name)
        zip_file_rel_path = os.path.join('data', 'contents', zip_res_file.file_name)
        unzip_file(self.user, self.composite_resource.short_id, zip_file_rel_path,
                   bool_remove_original=False)

        # resource should have 3 files now
        self.assertEqual(self.composite_resource.files.count(), 3)
        # there should not be any resource files ending with _meta.xml or _resmap.xml
        for res_file in self.composite_resource.files.all():
            self.assertFalse(res_file.file_name.endswith('_mata.xml'))
            self.assertFalse(res_file.file_name.endswith('_resmap.xml'))

    def test_unzip_rename(self):
        """Test that when a zip file gets unzipped at data/contents/ and the unzipped folder may be
         renamed without error (testing bug fix renaming a folder where a file exists that starts
         with the same name."""

        self.create_composite_resource()

        self.add_file_to_resource(file_to_add=self.zip_file)
        # resource should have 1 file now
        self.assertEqual(self.composite_resource.files.count(), 1)
        # unzip the above zip file  which should add one more file to the resource
        zip_res_file = ResourceFile.get(self.composite_resource, self.zip_file_name)
        zip_file_rel_path = os.path.join('data', 'contents', zip_res_file.file_name)
        unzip_file(self.user, self.composite_resource.short_id, zip_file_rel_path,
                   bool_remove_original=False)

        # resource should have 2 files now
        self.assertEqual(self.composite_resource.files.count(), 2)

        unzipped_folder = zip_file_rel_path.replace(".zip", "")
        renamed_folder = os.path.join('data', 'contents', "renamed")
        try:
            move_or_rename_file_or_folder(self.user, self.composite_resource.short_id,
                                          unzipped_folder, renamed_folder)
        except:
            self.fail("Exception thrown while renaming a folder.")

    def test_unzip_folder_clash(self):
        """Test that when a zip file gets unzipped a folder with the same
        name already exists, the existing folder is not overwritten """

        self.create_composite_resource()
        # add a zip file that contains only one file
        self.add_file_to_resource(file_to_add=self.zip_file)
        # resource should have 2 files now
        self.assertEqual(self.composite_resource.files.count(), 1)
        # unzip the above zip file  which should add one more file to the resource
        zip_res_file = ResourceFile.get(self.composite_resource, self.zip_file_name)
        zip_file_rel_path = os.path.join('data', 'contents', zip_res_file.file_name)
        unzip_file(self.user, self.composite_resource.short_id, zip_file_rel_path,
                   bool_remove_original=False)

        # resource should have 2 files now
        self.assertEqual(self.composite_resource.files.count(), 2)

        # unzip again
        unzip_file(self.user, self.composite_resource.short_id, zip_file_rel_path,
                   bool_remove_original=False)

        # ensure files aren't overwriting name clash
        self.assertEqual(self.composite_resource.files.count(), 3)

    def test_unzip_folder_clash_overwrite(self):
        """Test that when a zip file gets unzipped a folder with the same
        name already exists and overwrite is True, the existing folder is overwritten """

        self.create_composite_resource()
        # add a zip file that contains only one file
        self.add_file_to_resource(file_to_add=self.zip_file)

        self.assertEqual(self.composite_resource.files.count(), 1)
        # unzip the above zip file  which should add one more file to the resource
        zip_res_file = ResourceFile.get(self.composite_resource, self.zip_file_name)
        zip_file_rel_path = os.path.join('data', 'contents', zip_res_file.file_name)
        unzip_file(self.user, self.composite_resource.short_id, zip_file_rel_path,
                   bool_remove_original=False, overwrite=True)

        # resource should have 2 files now
        self.assertEqual(self.composite_resource.files.count(), 2)

        # unzip again
        unzip_file(self.user, self.composite_resource.short_id, zip_file_rel_path,
                   bool_remove_original=False, overwrite=True)

        # ensure files are overwriting
        self.assertEqual(self.composite_resource.files.count(), 2)

    def test_unzip_aggregation(self):
        """Test that when a zip file gets unzipped at data/contents/ where the contents includes a
        single file aggregation.  Testing the aggregation is recognized on unzip"""

        self.create_composite_resource()

        self.add_file_to_resource(file_to_add=self.zipped_aggregation_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        self.assertEqual(RefTimeseriesLogicalFile.objects.all().count(), 0)
        # unzip the above zip file  which should add one more file to the resource
        zip_file_rel_path = os.path.join('data', 'contents', self.zipped_aggregation_file_name)
        unzip_file(self.user, self.composite_resource.short_id, zip_file_rel_path,
                   bool_remove_original=False)

        # resource should have 2 files now
        self.assertEqual(self.composite_resource.files.count(), 2)
        # there should be a referenced time series now
        self.assertEqual(RefTimeseriesLogicalFile.objects.all().count(), 1)

    def test_unzip_aggregation_overwrite(self):
        """Test that when a zip file gets unzipped at data/contents/ where the contents includes a
        single file aggregation.  Testing aggregation is overwritten when overwrite is True"""

        self.create_composite_resource()

        self.add_file_to_resource(file_to_add=self.zipped_aggregation_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        self.assertEqual(RefTimeseriesLogicalFile.objects.all().count(), 0)
        # unzip the above zip file  which should add one more file to the resource
        zip_file_rel_path = os.path.join('data', 'contents', self.zipped_aggregation_file_name)
        unzip_file(self.user, self.composite_resource.short_id, zip_file_rel_path,
                   bool_remove_original=False, overwrite=True)

        # resource should have 2 files now
        self.assertEqual(self.composite_resource.files.count(), 2)
        # there should be a referenced time series now
        self.assertEqual(RefTimeseriesLogicalFile.objects.all().count(), 1)
        ref_time = RefTimeseriesLogicalFile.objects.first()
        ref_time.metadata.abstract = "overwritten"
        ref_time.metadata.save()

        self.assertEqual(RefTimeseriesLogicalFile.objects.first().metadata.abstract, "overwritten")

        unzip_file(self.user, self.composite_resource.short_id, zip_file_rel_path,
                   bool_remove_original=False, overwrite=True)

        # resource should still have 2 files
        self.assertEqual(self.composite_resource.files.count(), 2)
        # there should still be a referenced time series
        self.assertEqual(RefTimeseriesLogicalFile.objects.all().count(), 1)

        # check the file exists on disk after being overwritten
        for file in self.composite_resource.files.all():
            self.assertTrue(file.exists)

        self.assertNotEqual(RefTimeseriesLogicalFile.objects.first().metadata.abstract,
                            "overwritten")
