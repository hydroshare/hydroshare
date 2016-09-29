
import os
import tempfile
import shutil
from xml.etree import ElementTree as ET

from django.test import TransactionTestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.models import Group
from django.db import IntegrityError

from hs_core import hydroshare
from hs_core.hydroshare import utils
from hs_core.models import CoreMetaData, Creator, Contributor, Coverage, Rights, Title, Language, \
    Publisher, Identifier, Type, Subject, Description, Date, Format, Relation, Source
from hs_core.testing import MockIRODSTestCaseMixin
from hs_geo_raster_resource.models import RasterResource, OriginalCoverage, BandInformation, CellInformation


class TestRasterMetaData(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TestRasterMetaData, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        # even there is no file uploaded to resource, there are default extended automatically metadata created
        _, _, metadata, _ = utils.resource_pre_create_actions(resource_type='RasterResource',
                                                          resource_title='My Test Raster Resource',
                                                          page_redirect_url_key=None,
                                                          metadata=None,)
        self.resRaster = hydroshare.create_resource(
            resource_type='RasterResource',
            owner=self.user,
            title='My Test Raster Resource',
            metadata=metadata
        )

        self.temp_dir = tempfile.mkdtemp()
        self.raster_tif_file_name = 'raster_tif_valid.tif'
        self.raster_tif_file = 'hs_geo_raster_resource/tests/{}'.format(self.raster_tif_file_name)
        target_temp_raster_tif_file = os.path.join(self.temp_dir, self.raster_tif_file_name)
        shutil.copy(self.raster_tif_file, target_temp_raster_tif_file)
        self.raster_tif_file_obj = open(target_temp_raster_tif_file, 'r')

        self.raster_bad_tif_file_name = 'raster_tif_invalid.tif'
        self.raster_bad_tif_file = 'hs_geo_raster_resource/tests/{}'.format(self.raster_bad_tif_file_name)
        target_temp_raster_bad_tif_file = os.path.join(self.temp_dir, self.raster_bad_tif_file_name)
        shutil.copy(self.raster_bad_tif_file, target_temp_raster_bad_tif_file)
        self.raster_bad_tif_file_obj = open(target_temp_raster_bad_tif_file, 'r')

        self.raster_zip_file_name = 'raster_zip_valid.zip'
        self.raster_zip_file = 'hs_geo_raster_resource/tests/{}'.format(self.raster_zip_file_name)
        target_temp_raster_zip_file = os.path.join(self.temp_dir, self.raster_zip_file_name)
        shutil.copy(self.raster_zip_file, target_temp_raster_zip_file)
        self.raster_zip_file_obj = open(target_temp_raster_zip_file, 'r')

        self.raster_bad_zip_file_name = 'raster_zip_invalid.zip'
        self.raster_bad_zip_file = 'hs_geo_raster_resource/tests/{}'.format(self.raster_bad_zip_file_name)
        target_temp_raster_bad_zip_file = os.path.join(self.temp_dir, self.raster_bad_zip_file_name)
        shutil.copy(self.raster_bad_zip_file, target_temp_raster_bad_zip_file)
        self.raster_bad_zip_file_obj = open(target_temp_raster_bad_zip_file, 'r')

        temp_text_file = os.path.join(self.temp_dir, 'raster_text.txt')
        text_file = open(temp_text_file, 'w')
        text_file.write("Raster records")
        self.text_file_obj = open(temp_text_file, 'r')

    def tearDown(self):
        super(TestRasterMetaData, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_allowed_file_types(self):
        # test allowed file type is '.tif, .zip'
        self.assertIn('.tif', RasterResource.get_supported_upload_file_types())
        self.assertIn('.zip', RasterResource.get_supported_upload_file_types())
        self.assertEquals(len(RasterResource.get_supported_upload_file_types()), 2)

        # there should not be any content file
        self.assertEquals(self.resRaster.files.all().count(), 0)

        # trying to add a text file to this resource should raise exception
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resRaster, files=files, user=self.user,
                                                extract_metadata=False)

        # trying to add bad .tif file should raise file validation error
        files = [UploadedFile(file=self.raster_bad_tif_file_obj, name=self.raster_bad_tif_file_name)]
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resRaster, files=files, user=self.user,
                                                extract_metadata=False)

        # trying to add bad .zip file should raise file validation error
        files = [UploadedFile(file=self.raster_bad_zip_file_obj, name=self.raster_bad_zip_file_name)]
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resRaster, files=files, user=self.user,
                                                extract_metadata=False)

        # trying to add good .tif file should pass the file check
        files = [UploadedFile(file=self.raster_tif_file_obj, name=self.raster_tif_file_name)]
        utils.resource_file_add_pre_process(resource=self.resRaster, files=files, user=self.user,
                                            extract_metadata=False)
        utils.resource_file_add_process(resource=self.resRaster, files=files, user=self.user,
                                        extract_metadata=False)

        # there should be 2 content file: with .vrt file created by system
        self.assertEquals(self.resRaster.files.all().count(), 2)
        file_names = [os.path.basename(f.resource_file.name) for f in self.resRaster.files.all()]
        self.assertIn('raster_tif_valid.vrt', file_names)

        # delete content file that we added above
        hydroshare.delete_resource_file(self.resRaster.short_id, self.raster_tif_file_name, self.user)

        # there should be no content file
        self.assertEqual(self.resRaster.files.all().count(), 0)

        # trying to add good .zip file should pass the file check
        files = [UploadedFile(file=self.raster_zip_file_obj, name=self.raster_zip_file_name)]
        utils.resource_file_add_pre_process(resource=self.resRaster, files=files, user=self.user,
                                            extract_metadata=False)
        utils.resource_file_add_process(resource=self.resRaster, files=files, user=self.user,
                                        extract_metadata=False)

        # there should be 10 content file:
        self.assertEqual(self.resRaster.files.all().count(), 10)

        # file pre add process should raise validation error if we try to add a 2nd file when the resource has
        # already content files
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resRaster, files=files, user=self.user,
                                                extract_metadata=False)

    def test_metadata_initialization_for_empty_resource(self):
        # there should be default cell information:
        cell_info = self.resRaster.metadata.cellInformation
        self.assertNotEqual(cell_info, None)
        self.assertEquals(cell_info.rows, None)
        self.assertEquals(cell_info.columns, None)
        self.assertEquals(cell_info.cellSizeXValue, None)
        self.assertEquals(cell_info.cellSizeYValue, None)
        self.assertEquals(cell_info.cellDataType, None)


        # there should be default spatial reference info
        ori_coverage = self.resRaster.metadata.originalCoverage
        self.assertNotEquals(ori_coverage, None)
        self.assertEquals(ori_coverage.value['northlimit'], None)
        self.assertEquals(ori_coverage.value['eastlimit'], None)
        self.assertEquals(ori_coverage.value['southlimit'], None)
        self.assertEquals(ori_coverage.value['westlimit'], None)
        self.assertEquals(ori_coverage.value['units'], None)
        self.assertEquals(ori_coverage.value['projection'], None)

        # there should be default band information:
        band_info = self.resRaster.metadata.bandInformation.first()
        self.assertNotEqual(band_info, 0)
        self.assertEquals(band_info.variableName, None)
        self.assertEquals(band_info.variableUnit, None)

    def test_metadata_extraction_on_resource_creation(self):
        # passing the file object that points to the temp dir doesn't work - create_resource throws error
        # open the file from the fixed file location
        files = [UploadedFile(file=self.raster_tif_file_obj, name=self.raster_tif_file_name)]
        _, _, metadata, _ = utils.resource_pre_create_actions(resource_type='RasterResource',
                                                          resource_title='My Test Raster Resource',
                                                          page_redirect_url_key=None,
                                                          files=files,
                                                          metadata=None,)
        self.resRaster = hydroshare.create_resource(
            'RasterResource',
            self.user,
            'My Test Raster Resource',
            files=files,
            metadata=metadata
            )

        self._test_metadata_extraction()

    def test_metadata_extraction_on_content_file_add(self):
        # test the core metadata at this point
        self.assertEquals(self.resRaster.metadata.title.value, 'My Test Raster Resource')

        # there shouldn't any abstract element
        self.assertEquals(self.resRaster.metadata.description, None)

        # there shouldn't any coverage element
        self.assertEquals(self.resRaster.metadata.coverages.all().count(), 0)

        # there shouldn't any format element
        self.assertEquals(self.resRaster.metadata.formats.all().count(), 0)

        # there shouldn't any subject element
        self.assertEquals(self.resRaster.metadata.subjects.all().count(), 0)

        # there shouldn't any contributor element
        self.assertEquals(self.resRaster.metadata.contributors.all().count(), 0)

        # there should be default extended metadata
        self.assertNotEquals(self.resRaster.metadata.originalCoverage, None)
        self.assertNotEquals(self.resRaster.metadata.cellInformation, None)
        self.assertNotEquals(self.resRaster.metadata.bandInformation, None)

        # adding a valid tiff file should generate some core metadata and all extended metadata
        files = [UploadedFile(file=self.raster_tif_file_obj, name=self.raster_tif_file_name)]
        utils.resource_file_add_pre_process(resource=self.resRaster, files=files, user=self.user,
                                            extract_metadata=False)
        utils.resource_file_add_process(resource=self.resRaster, files=files, user=self.user,
                                        extract_metadata=False)

        self._test_metadata_extraction()
    
    def test_metadata_on_content_file_delete(self):
        # test that some of the metadata is not deleted on content file deletion
        files = [UploadedFile(file=self.raster_tif_file_obj, name=self.raster_tif_file_name)]
        utils.resource_file_add_pre_process(resource=self.resRaster, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resRaster, files=files, user=self.user,
                                        extract_metadata=True)
        # there should be 2 content files
        self.assertEquals(self.resRaster.files.all().count(), 2)

        # there should be 2 format elements
        self.assertEquals(self.resRaster.metadata.formats.all().count(), 2)
        self.assertEquals(self.resRaster.metadata.formats.all().filter(value='application/vrt').count(), 1)
        self.assertEquals(self.resRaster.metadata.formats.all().filter(value='image/tiff').count(), 1)

        # delete content file that we added above
        hydroshare.delete_resource_file(self.resRaster.short_id, self.raster_tif_file_name, self.user)

        # there should no content file
        self.assertEquals(self.resRaster.files.all().count(), 0)

        # there should be a title element
        self.assertNotEquals(self.resRaster.metadata.title, None)

        # there should be no abstract element
        self.assertEquals(self.resRaster.metadata.description, None)

        # there should be 1 creator element
        self.assertEquals(self.resRaster.metadata.creators.all().count(), 1)

        # there should be no contributor element
        self.assertEquals(self.resRaster.metadata.contributors.all().count(), 0)

        # there should be no coverage element
        self.assertEquals(self.resRaster.metadata.coverages.all().count(), 0)

        # there should be no format element
        self.assertEquals(self.resRaster.metadata.formats.all().count(), 0)

        # there should be no subject element
        self.assertEquals(self.resRaster.metadata.subjects.all().count(), 0)

        # testing extended metadata elements
        self.assertEquals(self.resRaster.metadata.originalCoverage, None)
        self.assertNotEquals(self.resRaster.metadata.cellInformation, None)
        self.assertNotEquals(self.resRaster.metadata.bandInformation.count, 0)

    def test_metadata_delete_on_resource_delete(self):
        # adding a valid raster tif file should generate some core metadata and all extended metadata
        files = [UploadedFile(file=self.raster_tif_file_obj, name=self.raster_tif_file_name)]
        utils.resource_file_add_pre_process(resource=self.resRaster, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resRaster, files=files, user=self.user,
                                        extract_metadata=True)

        # before resource delete
        # resource core metadata
        raster_metadata_obj = self.resRaster.metadata
        self.assertEquals(CoreMetaData.objects.all().count(), 1)
        # there should be Creator metadata objects
        self.assertTrue(Creator.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Contributor metadata objects
        self.assertFalse(Contributor.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be Identifier metadata objects
        self.assertTrue(Identifier.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be Type metadata objects
        self.assertTrue(Type.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Source metadata objects
        self.assertFalse(Source.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Relation metadata objects
        self.assertFalse(Relation.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Publisher metadata objects
        self.assertFalse(Publisher.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be Title metadata objects
        self.assertTrue(Title.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Description (Abstract) metadata objects
        self.assertFalse(Description.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be Date metadata objects
        self.assertTrue(Date.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Subject metadata objects
        self.assertFalse(Subject.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be Coverage metadata objects
        self.assertTrue(Coverage.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be Format metadata objects
        self.assertTrue(Format.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be Language metadata objects
        self.assertTrue(Language.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be Rights metadata objects
        self.assertTrue(Rights.objects.filter(object_id=raster_metadata_obj.id).exists())

        # resource specific metadata
        # there should be original coverage metadata objects
        self.assertTrue(OriginalCoverage.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be CellInformation metadata objects
        self.assertTrue(CellInformation.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be BandInformation metadata objects
        self.assertTrue(BandInformation.objects.filter(object_id=raster_metadata_obj.id).exists())

        # delete resource
        hydroshare.delete_resource(self.resRaster.short_id)
        self.assertEquals(CoreMetaData.objects.all().count(), 0)

        # there should be no Creator metadata objects
        self.assertFalse(Creator.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Contributor metadata objects
        self.assertFalse(Contributor.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Identifier metadata objects
        self.assertFalse(Identifier.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Type metadata objects
        self.assertFalse(Type.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Source metadata objects
        self.assertFalse(Source.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Relation metadata objects
        self.assertFalse(Relation.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Publisher metadata objects
        self.assertFalse(Publisher.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Title metadata objects
        self.assertFalse(Title.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Description (Abstract) metadata objects
        self.assertFalse(Description.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Date metadata objects
        self.assertFalse(Date.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Subject metadata objects
        self.assertFalse(Subject.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Coverage metadata objects
        self.assertFalse(Coverage.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Format metadata objects
        self.assertFalse(Format.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Language metadata objects
        self.assertFalse(Language.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be no Rights metadata objects
        self.assertFalse(Rights.objects.filter(object_id=raster_metadata_obj.id).exists())

        # resource specific metadata
        # there should be no original coverage metadata objects
        self.assertFalse(OriginalCoverage.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be CellInformation metadata objects
        self.assertFalse(CellInformation.objects.filter(object_id=raster_metadata_obj.id).exists())
        # there should be bandInformation metadata objects
        self.assertFalse(BandInformation.objects.filter(object_id=raster_metadata_obj.id).exists())

    def test_extended_metadata_CRUD(self):
        # delete default original coverage metadata
        self.assertNotEquals(self.resRaster.metadata.originalCoverage, None)
        self.resRaster.metadata.originalCoverage.delete()

        # create new original coverage metadata with meaningful value
        value = {"northlimit": 12, "projection": "transverse_mercator", "units": "meter", "southlimit": 10,
                "eastlimit": 23, "westlimit": 2}
        self.resRaster.metadata.create_element('originalcoverage', value=value)

        self.assertEquals(self.resRaster.metadata.originalCoverage.value, value)

        # multiple original coverage elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resRaster.metadata.create_element('originalcoverage', value=value)

        # delete default cell information element
        self.assertNotEquals(self.resRaster.metadata.cellInformation, None)
        self.resRaster.metadata.cellInformation.delete()

        # create new cell information metadata with meaningful value
        self.resRaster.metadata.create_element('cellinformation', name='cellinfo', cellDataType='Float32',
                                                   rows=1660, columns=985, cellSizeXValue=30.0, cellSizeYValue=30.0,
                                               )

        cell_info = self.resRaster.metadata.cellInformation
        self.assertEquals(cell_info.rows, 1660)
        self.assertEquals(cell_info.columns, 985)
        self.assertEquals(cell_info.cellSizeXValue, 30.0)
        self.assertEquals(cell_info.cellSizeYValue, 30.0)
        self.assertEquals(cell_info.cellDataType, 'Float32')


        # multiple cell Information elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resRaster.metadata.create_element('cellinformation', name='cellinfo', cellDataType='Float32',
                                                   rows=1660, columns=985,
                                                   cellSizeXValue=30.0, cellSizeYValue=30.0,
                                                   )

        # delete default band information element
        self.assertNotEquals(self.resRaster.metadata.bandInformation, None)
        self.resRaster.metadata.bandInformation.first().delete()

        # create band information element with meaningful value
        self.resRaster.metadata.create_element('bandinformation', name='bandinfo',
                                               variableName='diginal elevation',
                                               variableUnit='meter',
                                               method='this is method',
                                               comment='this is comment',
                                               maximumValue=1000, minimumValue=0, noDataValue=-9999)

        band_info = self.resRaster.metadata.bandInformation.first()
        self.assertEquals(band_info.name, 'bandinfo')
        self.assertEquals(band_info.variableName, 'diginal elevation')
        self.assertEquals(band_info.variableUnit, 'meter')
        self.assertEquals(band_info.method, 'this is method')
        self.assertEquals(band_info.comment, 'this is comment')
        self.assertEquals(band_info.maximumValue, '1000')
        self.assertEquals(band_info.minimumValue, '0')
        self.assertEquals(band_info.noDataValue, '-9999')

        # multiple band information elements are allowed
        self.resRaster.metadata.create_element('bandinformation', name='bandinfo',
                                               variableName='diginal elevation2',
                                               variableUnit='meter',
                                               method='this is method',
                                               comment='this is comment',
                                               maximumValue=1000, minimumValue=0, noDataValue=-9999)
        self.assertEquals(self.resRaster.metadata.bandInformation.all().count(), 2)

        # delete
        # original coverage deletion is not allowed
        with self.assertRaises(ValidationError):
            self.resRaster.metadata.delete_element('originalcoverage', self.resRaster.metadata.originalCoverage.id)

        # cell information deletion is not allowed
        with self.assertRaises(ValidationError):
            self.resRaster.metadata.delete_element('cellinformation', self.resRaster.metadata.cellInformation.id)

        # band information deletion is not allowed
        with self.assertRaises(ValidationError):
            self.resRaster.metadata.delete_element('bandinformation', self.resRaster.metadata.bandInformation.first().id)

        # update
        # update original coverage element
        value_2 = {"northlimit": 12.5, "projection": "transverse_mercator", "units": "meter", "southlimit": 10.5,
                    "eastlimit": 23.5, "westlimit": 2.5}
        self.resRaster.metadata.update_element('originalcoverage', self.resRaster.metadata.originalCoverage.id, value=value_2)

        self.assertEquals(self.resRaster.metadata.originalCoverage.value, value_2)

        # update cell info element
        self.resRaster.metadata.update_element('cellinformation',
                                               self.resRaster.metadata.cellInformation.id,
                                               name='cellinfo', cellDataType='Double',
                                               rows=166, columns=98,
                                               cellSizeXValue=3.0, cellSizeYValue=3.0,
                                               )

        cell_info = self.resRaster.metadata.cellInformation
        self.assertEquals(cell_info.rows, 166)
        self.assertEquals(cell_info.columns, 98)
        self.assertEquals(cell_info.cellSizeXValue, 3.0)
        self.assertEquals(cell_info.cellSizeYValue, 3.0)
        self.assertEquals(cell_info.cellDataType, 'Double')


        # update band info element
        self.resRaster.metadata.update_element('bandinformation',
                                               self.resRaster.metadata.bandInformation.first().id,
                                               name='bandinfo',
                                               variableName='precipitation',
                                               variableUnit='mm/h',
                                               method='this is method2',
                                               comment='this is comment2',
                                               maximumValue=1001, minimumValue=1, noDataValue=-9998
                                               )

        band_info = self.resRaster.metadata.bandInformation.first()
        self.assertEquals(band_info.name, 'bandinfo')
        self.assertEquals(band_info.variableName, 'precipitation')
        self.assertEquals(band_info.variableUnit, 'mm/h')
        self.assertEquals(band_info.method, 'this is method2')
        self.assertEquals(band_info.comment, 'this is comment2')
        self.assertEquals(band_info.maximumValue, '1001')
        self.assertEquals(band_info.minimumValue, '1')
        self.assertEquals(band_info.noDataValue, '-9998')

    def test_get_xml(self):
        # add a valid raster file to generate metadata
        files = [UploadedFile(file=self.raster_tif_file_obj, name=self.raster_tif_file_name)]
        utils.resource_file_add_pre_process(resource=self.resRaster, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resRaster, files=files, user=self.user,
                                        extract_metadata=True)

        # test if xml from get_xml() is well formed
        ET.fromstring(self.resRaster.metadata.get_xml())

    def test_can_have_multiple_content_files(self):
        self.assertFalse(RasterResource.can_have_multiple_files())

    def test_can_upload_multiple_content_files(self):
        # only one file can be uploaded
        self.assertFalse(RasterResource.allow_multiple_file_upload())

    def test_public_or_discoverable(self):
        self.assertFalse(self.resRaster.has_required_content_files())
        self.assertFalse(self.resRaster.metadata.has_all_required_elements())
        self.assertFalse(self.resRaster.can_be_public_or_discoverable)

        # adding a valid raster file
        files = [UploadedFile(file=self.raster_tif_file_obj, name=self.raster_tif_file_name)]
        utils.resource_file_add_pre_process(resource=self.resRaster, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resRaster, files=files, user=self.user,
                                        extract_metadata=True)

        # adding required metadata
        self.resRaster.metadata.create_element('description', abstract='example abstract')
        self.resRaster.metadata.create_element('subject',value='logan')

        self.assertTrue(self.resRaster.has_required_content_files())
        self.assertTrue(self.resRaster.metadata.has_all_required_elements())
        self.assertTrue(self.resRaster.can_be_public_or_discoverable)

    def _test_metadata_extraction(self):

        # there should be 2 content files
        self.assertEquals(self.resRaster.files.all().count(), 2)

        # test core metadata after metadata extraction
        extracted_title = "My Test Raster Resource"
        self.assertEquals(self.resRaster.metadata.title.value, extracted_title)

        # there should be 1 creator
        self.assertEquals(self.resRaster.metadata.creators.all().count(), 1)

        # there should be 1 coverage element - box type
        self.assertEquals(self.resRaster.metadata.coverages.all().count(), 1)
        self.assertEquals(self.resRaster.metadata.coverages.all().filter(type='box').count(), 1)

        box_coverage = self.resRaster.metadata.coverages.all().filter(type='box').first()
        self.assertEquals(box_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEquals(box_coverage.value['units'], 'Decimal degrees')
        self.assertEquals(box_coverage.value['northlimit'], 42.11071605314457)
        self.assertEquals(box_coverage.value['eastlimit'], -111.45699925047542)
        self.assertEquals(box_coverage.value['southlimit'], 41.66417975061928)
        self.assertEquals(box_coverage.value['westlimit'], -111.81761887121905)

        # there should be 2 format elements
        self.assertEquals(self.resRaster.metadata.formats.all().count(), 2)
        self.assertEquals(self.resRaster.metadata.formats.all().filter(value='application/vrt').count(), 1)
        self.assertEquals(self.resRaster.metadata.formats.all().filter(value='image/tiff').count(), 1)

        # testing extended metadata element: original coverage
        ori_coverage = self.resRaster.metadata.originalCoverage
        self.assertNotEquals(ori_coverage, None)
        self.assertEquals(ori_coverage.value['northlimit'], 4662392.446916306)
        self.assertEquals(ori_coverage.value['eastlimit'], 461954.01909127034)
        self.assertEquals(ori_coverage.value['southlimit'], 4612592.446916306)
        self.assertEquals(ori_coverage.value['westlimit'], 432404.01909127034)
        self.assertEquals(ori_coverage.value['units'], 'meter')
        self.assertEquals(ori_coverage.value['projection'], 'NAD83 / UTM zone 12N Transverse_Mercator')

        # testing extended metadata element: cell information
        cell_info = self.resRaster.metadata.cellInformation
        self.assertEquals(cell_info.rows, 1660)
        self.assertEquals(cell_info.columns, 985)
        self.assertEquals(cell_info.cellSizeXValue, 30.0)
        self.assertEquals(cell_info.cellSizeYValue, 30.0)
        self.assertEquals(cell_info.cellDataType, 'Float32')

        # testing extended metadata element: band information
        self.assertEquals(self.resRaster.metadata.bandInformation.count(), 1)
        band_info = self.resRaster.metadata.bandInformation.first()
        self.assertEquals(band_info.noDataValue, '-3.40282346639e+38')
        self.assertEquals(band_info.maximumValue, '3031.44311523')
        self.assertEquals(band_info.minimumValue, '1358.33459473')


