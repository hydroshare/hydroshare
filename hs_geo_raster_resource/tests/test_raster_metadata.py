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

from hs_core.testing import MockIRODSTestCaseMixin, TestCaseCommonUtilities
from hs_geo_raster_resource.models import RasterResource, OriginalCoverage, BandInformation, \
    CellInformation


class TestRasterMetaData(MockIRODSTestCaseMixin, TestCaseCommonUtilities, TransactionTestCase):
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

        self.resRaster = hydroshare.create_resource(
            resource_type='RasterResource',
            owner=self.user,
            title='My Test Raster Resource'
        )

        self.temp_dir = tempfile.mkdtemp()
        self.raster_tif_file_name = 'raster_tif_valid.tif'
        self.raster_tif_file = 'hs_geo_raster_resource/tests/{}'.format(self.raster_tif_file_name)
        target_temp_raster_tif_file = os.path.join(self.temp_dir, self.raster_tif_file_name)
        shutil.copy(self.raster_tif_file, target_temp_raster_tif_file)
        self.raster_tif_file_obj = open(target_temp_raster_tif_file, 'r')

        self.raster_bad_tif_file_name = 'raster_tif_invalid.tif'
        self.raster_bad_tif_file = 'hs_geo_raster_resource/tests/{}'.format(
            self.raster_bad_tif_file_name)
        target_temp_raster_bad_tif_file = os.path.join(self.temp_dir, self.raster_bad_tif_file_name)
        shutil.copy(self.raster_bad_tif_file, target_temp_raster_bad_tif_file)
        self.raster_bad_tif_file_obj = open(target_temp_raster_bad_tif_file, 'r')

        self.raster_zip_file_name = 'raster_zip_valid.zip'
        self.raster_zip_file = 'hs_geo_raster_resource/tests/{}'.format(self.raster_zip_file_name)
        target_temp_raster_zip_file = os.path.join(self.temp_dir, self.raster_zip_file_name)
        shutil.copy(self.raster_zip_file, target_temp_raster_zip_file)
        self.raster_zip_file_obj = open(target_temp_raster_zip_file, 'r')

        self.raster_bad_zip_file_name = 'raster_zip_invalid.zip'
        self.raster_bad_zip_file = 'hs_geo_raster_resource/tests/{}'.format(
            self.raster_bad_zip_file_name)
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
        self.assertEqual(len(RasterResource.get_supported_upload_file_types()), 2)

        # there should not be any content file
        self.assertEqual(self.resRaster.files.all().count(), 0)

        # trying to add a text file to this resource should raise exception
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_process(resource=self.resRaster, files=files,
                                            user=self.user,
                                            extract_metadata=False)

        # trying to add bad .tif file should raise file validation error
        files = [UploadedFile(file=self.raster_bad_tif_file_obj,
                              name=self.raster_bad_tif_file_name)]
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_process(resource=self.resRaster, files=files,
                                            user=self.user, extract_metadata=False)

        # trying to add bad .zip file should raise file validation error
        files = [UploadedFile(file=self.raster_bad_zip_file_obj,
                              name=self.raster_bad_zip_file_name)]
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_process(resource=self.resRaster, files=files,
                                            user=self.user, extract_metadata=False)

        # trying to add good .tif file should pass the file check
        files = [UploadedFile(file=self.raster_tif_file_obj, name=self.raster_tif_file_name)]
        utils.resource_file_add_process(resource=self.resRaster, files=files, user=self.user,
                                        extract_metadata=False)

        # there should be 2 content file: with .vrt file created by system
        self.assertEqual(self.resRaster.files.all().count(), 2)
        file_names = [os.path.basename(f.resource_file.name) for f in self.resRaster.files.all()]
        self.assertIn('raster_tif_valid.vrt', file_names)

        # delete content file that we added above
        hydroshare.delete_resource_file(self.resRaster.short_id, self.raster_tif_file_name,
                                        self.user)

        # there should be no content file
        self.assertEqual(self.resRaster.files.all().count(), 0)

        # trying to add good .zip file should pass the file check
        files = [UploadedFile(file=self.raster_zip_file_obj, name=self.raster_zip_file_name)]
        utils.resource_file_add_process(resource=self.resRaster, files=files, user=self.user,
                                        extract_metadata=False)

        # there should be 10 content file:
        self.assertEqual(self.resRaster.files.all().count(), 10)

        # file pre add process should raise validation error if we try to add a 2nd file when
        # the resource has already content files
        with self.assertRaises(utils.ResourceFileValidationException):
            utils.resource_file_add_pre_process(resource=self.resRaster, files=files,
                                                user=self.user, extract_metadata=False)

    def test_metadata_extraction_on_resource_creation(self):
        # passing the file object that points to the temp dir doesn't work - create_resource throws
        # error. open the file from the fixed file location

        files = [UploadedFile(file=self.raster_tif_file_obj, name=self.raster_tif_file_name)]

        self.resRaster = hydroshare.create_resource(
            'RasterResource',
            self.user,
            'My Test Raster Resource',
            files=files,
            metadata=[]
            )
        # uploaded file validation and metadata extraction happens in post resource
        # creation handler
        utils.resource_post_create_actions(resource=self.resRaster, user=self.user, metadata=[])
        super(TestRasterMetaData, self).raster_metadata_extraction()

    def test_metadata_extraction_on_content_file_add(self):
        # test the core metadata at this point
        self.assertEqual(self.resRaster.metadata.title.value, 'My Test Raster Resource')

        # there shouldn't any abstract element
        self.assertEqual(self.resRaster.metadata.description, None)

        # there shouldn't any coverage element
        self.assertEqual(self.resRaster.metadata.coverages.all().count(), 0)

        # there shouldn't any format element
        self.assertEqual(self.resRaster.metadata.formats.all().count(), 0)

        # there shouldn't any subject element
        self.assertEqual(self.resRaster.metadata.subjects.all().count(), 0)

        # there shouldn't any contributor element
        self.assertEqual(self.resRaster.metadata.contributors.all().count(), 0)

        # there should not be any extended metadata
        self.assertEqual(self.resRaster.metadata.originalCoverage, None)
        self.assertEqual(self.resRaster.metadata.cellInformation, None)
        self.assertEqual(self.resRaster.metadata.bandInformations.count(), 0)

        # adding a valid tiff file should generate some core metadata and all extended metadata
        files = [UploadedFile(file=self.raster_tif_file_obj, name=self.raster_tif_file_name)]
        utils.resource_file_add_process(resource=self.resRaster, files=files, user=self.user,
                                        extract_metadata=False)

        super(TestRasterMetaData, self).raster_metadata_extraction()

    def test_metadata_on_content_file_delete(self):
        # test that some of the metadata is not deleted on content file deletion
        files = [UploadedFile(file=self.raster_tif_file_obj, name=self.raster_tif_file_name)]
        utils.resource_file_add_pre_process(resource=self.resRaster, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resRaster, files=files, user=self.user,
                                        extract_metadata=True)
        # there should be 2 content files
        self.assertEqual(self.resRaster.files.all().count(), 2)

        # there should be 2 format elements
        self.assertEqual(self.resRaster.metadata.formats.all().count(), 2)
        self.assertEqual(self.resRaster.metadata.formats.all().filter(
            value='application/vrt').count(), 1)

        self.assertEqual(self.resRaster.metadata.formats.all().filter(
            value='image/tiff').count(), 1)

        # delete content file that we added above
        hydroshare.delete_resource_file(self.resRaster.short_id, self.raster_tif_file_name,
                                        self.user)

        # there should no content file
        self.assertEqual(self.resRaster.files.all().count(), 0)

        # there should be a title element
        self.assertNotEqual(self.resRaster.metadata.title, None)

        # there should be no abstract element
        self.assertEqual(self.resRaster.metadata.description, None)

        # there should be 1 creator element
        self.assertEqual(self.resRaster.metadata.creators.all().count(), 1)

        # there should be no contributor element
        self.assertEqual(self.resRaster.metadata.contributors.all().count(), 0)

        # there should be no coverage element
        self.assertEqual(self.resRaster.metadata.coverages.all().count(), 0)

        # there should be no format element
        self.assertEqual(self.resRaster.metadata.formats.all().count(), 0)

        # there should be no subject element
        self.assertEqual(self.resRaster.metadata.subjects.all().count(), 0)

        # testing extended metadata elements - there should not be any resource specific metadata
        self.assertEqual(self.resRaster.metadata.originalCoverage, None)

        self.assertEqual(self.resRaster.metadata.cellInformation, None)
        self.assertEqual(self.resRaster.metadata.bandInformations.count(), 0)

    def test_metadata_delete_on_resource_delete(self):
        # adding a valid raster tif file should generate some core metadata and all extended
        # metadata
        files = [UploadedFile(file=self.raster_tif_file_obj, name=self.raster_tif_file_name)]
        utils.resource_file_add_process(resource=self.resRaster, files=files, user=self.user,
                                        extract_metadata=True)

        # before resource delete
        # resource core metadata
        raster_metadata_obj = self.resRaster.metadata
        self.assertEqual(CoreMetaData.objects.all().count(), 1)
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
        self.assertEqual(CoreMetaData.objects.all().count(), 0)

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
        # create new original coverage metadata with meaningful value
        value = {"northlimit": 12, "projection": "transverse_mercator", "units": "meter",
                 "southlimit": 10, "eastlimit": 23, "westlimit": 2}
        self.resRaster.metadata.create_element('originalcoverage', value=value)

        self.assertEqual(self.resRaster.metadata.originalCoverage.value, value)

        # multiple original coverage elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resRaster.metadata.create_element('originalcoverage', value=value)

        # create new cell information metadata with meaningful value
        self.resRaster.metadata.create_element('cellinformation', name='cellinfo',
                                               cellDataType='Float32',
                                               rows=1660, columns=985, cellSizeXValue=30.0,
                                               cellSizeYValue=30.0,
                                               )

        cell_info = self.resRaster.metadata.cellInformation
        self.assertEqual(cell_info.rows, 1660)
        self.assertEqual(cell_info.columns, 985)
        self.assertEqual(cell_info.cellSizeXValue, 30.0)
        self.assertEqual(cell_info.cellSizeYValue, 30.0)
        self.assertEqual(cell_info.cellDataType, 'Float32')

        # multiple cell Information elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resRaster.metadata.create_element('cellinformation', name='cellinfo',
                                                   cellDataType='Float32',
                                                   rows=1660, columns=985,
                                                   cellSizeXValue=30.0, cellSizeYValue=30.0,
                                                   )

        # create band information element with meaningful value
        self.resRaster.metadata.create_element('bandinformation', name='bandinfo',
                                               variableName='diginal elevation',
                                               variableUnit='meter',
                                               method='this is method',
                                               comment='this is comment',
                                               maximumValue=1000, minimumValue=0, noDataValue=-9999)

        band_info = self.resRaster.metadata.bandInformations.first()
        self.assertEqual(band_info.name, 'bandinfo')
        self.assertEqual(band_info.variableName, 'diginal elevation')
        self.assertEqual(band_info.variableUnit, 'meter')
        self.assertEqual(band_info.method, 'this is method')
        self.assertEqual(band_info.comment, 'this is comment')
        self.assertEqual(band_info.maximumValue, '1000')
        self.assertEqual(band_info.minimumValue, '0')
        self.assertEqual(band_info.noDataValue, '-9999')

        # multiple band information elements are allowed
        self.resRaster.metadata.create_element('bandinformation', name='bandinfo',
                                               variableName='diginal elevation2',
                                               variableUnit='meter',
                                               method='this is method',
                                               comment='this is comment',
                                               maximumValue=1000, minimumValue=0, noDataValue=-9999)
        self.assertEqual(self.resRaster.metadata.bandInformations.all().count(), 2)

        # delete
        # original coverage deletion is not allowed
        with self.assertRaises(ValidationError):
            self.resRaster.metadata.delete_element('originalcoverage',
                                                   self.resRaster.metadata.originalCoverage.id)

        # cell information deletion is not allowed
        with self.assertRaises(ValidationError):
            self.resRaster.metadata.delete_element('cellinformation',
                                                   self.resRaster.metadata.cellInformation.id)

        # band information deletion is not allowed
        with self.assertRaises(ValidationError):
            self.resRaster.metadata.delete_element(
                'bandinformation',
                self.resRaster.metadata.bandInformations.first().id)

        # update
        # update original coverage element
        value_2 = {"northlimit": 12.5, "projection": "transverse_mercator", "units": "meter",
                   "southlimit": 10.5, "eastlimit": 23.5, "westlimit": 2.5}
        self.resRaster.metadata.update_element('originalcoverage',
                                               self.resRaster.metadata.originalCoverage.id,
                                               value=value_2)

        self.assertEqual(self.resRaster.metadata.originalCoverage.value, value_2)

        # update cell info element
        self.resRaster.metadata.update_element('cellinformation',
                                               self.resRaster.metadata.cellInformation.id,
                                               name='cellinfo', cellDataType='Double',
                                               rows=166, columns=98,
                                               cellSizeXValue=3.0, cellSizeYValue=3.0,
                                               )

        cell_info = self.resRaster.metadata.cellInformation
        self.assertEqual(cell_info.rows, 166)
        self.assertEqual(cell_info.columns, 98)
        self.assertEqual(cell_info.cellSizeXValue, 3.0)
        self.assertEqual(cell_info.cellSizeYValue, 3.0)
        self.assertEqual(cell_info.cellDataType, 'Double')

        # update band info element
        self.resRaster.metadata.update_element('bandinformation',
                                               self.resRaster.metadata.bandInformations.first().id,
                                               name='bandinfo',
                                               variableName='precipitation',
                                               variableUnit='mm/h',
                                               method='this is method2',
                                               comment='this is comment2',
                                               maximumValue=1001, minimumValue=1,
                                               noDataValue=-9998)

        band_info = self.resRaster.metadata.bandInformations.first()
        self.assertEqual(band_info.name, 'bandinfo')
        self.assertEqual(band_info.variableName, 'precipitation')
        self.assertEqual(band_info.variableUnit, 'mm/h')
        self.assertEqual(band_info.method, 'this is method2')
        self.assertEqual(band_info.comment, 'this is comment2')
        self.assertEqual(band_info.maximumValue, '1001')
        self.assertEqual(band_info.minimumValue, '1')
        self.assertEqual(band_info.noDataValue, '-9998')

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
        self.resRaster.metadata.create_element('subject', value='logan')

        self.assertTrue(self.resRaster.has_required_content_files())
        self.assertTrue(self.resRaster.metadata.has_all_required_elements())
        self.assertTrue(self.resRaster.can_be_public_or_discoverable)
