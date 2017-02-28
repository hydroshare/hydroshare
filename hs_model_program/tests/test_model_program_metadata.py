import os
import tempfile
import shutil
from xml.etree import ElementTree as ET

from django.test import TransactionTestCase
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.models import Group

from hs_core import hydroshare
from hs_core.hydroshare import utils
from hs_core.models import CoreMetaData, Creator, Contributor, Coverage, Rights, Title, Language, \
    Publisher, Identifier, Type, Subject, Description, Date, Format, Relation, Source
from hs_core.testing import MockIRODSTestCaseMixin
from hs_model_program.models import ModelProgramResource, MpMetadata


class TestModelProgramMetaData(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TestModelProgramMetaData, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.resModelProgram = hydroshare.create_resource(
            resource_type='ModelProgramResource',
            owner=self.user,
            title='Test Model Program Resource'
        )

        self.temp_dir = tempfile.mkdtemp()

        self.file_name = "MP.txt"
        temp_text_file = os.path.join(self.temp_dir, self.file_name)
        text_file = open(temp_text_file, 'w')
        text_file.write("Model Program resource files")
        self.text_file_obj = open(temp_text_file, 'r')

        self.file_name_2 = "MP.csv"
        temp_text_file = os.path.join(self.temp_dir, self.file_name_2)
        text_file = open(temp_text_file, 'w')
        text_file.write("Model,Program,resource,files")
        self.text_file_obj_2 = open(temp_text_file, 'r')

    def tearDown(self):
        super(TestModelProgramMetaData, self).tearDown()
        # for f in self.resModelProgram.files.all():
        #     resource.delete_resource_file(self.resModelProgram.short_id, f.short_path, self.user)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_allowed_file_types(self):
        # test allowed file type is '.*'
        self.assertEquals(self.resModelProgram.get_supported_upload_file_types(), '.*')

        # there should not be any content file
        self.assertEquals(self.resModelProgram.files.all().count(), 0)

        # Upload any file type should pass both the file pre add check and post add check
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resModelProgram, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resModelProgram, files=files,
                                        user=self.user, extract_metadata=False)

        # there should one content file
        self.assertEquals(self.resModelProgram.files.all().count(), 1)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resModelProgram.metadata.program, None)

        # Uploading any other file type should pass both the file pre add check post add check
        files = [UploadedFile(file=self.text_file_obj_2, name=self.text_file_obj_2.name)]
        utils.resource_file_add_pre_process(resource=self.resModelProgram, files=files,
                                            user=self.user, extract_metadata=True)

        utils.resource_file_add_process(resource=self.resModelProgram, files=files,
                                        user=self.user, extract_metadata=True)

        # there should two content files
        self.assertEquals(self.resModelProgram.files.all().count(), 2)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resModelProgram.metadata.program, None)

    def test_extended_metadata_CRUD(self):
        # test the core metadata at this point
        # there should be a title element
        self.assertEquals(self.resModelProgram.metadata.title.value, 'Test Model Program Resource')

        # there should be a creator element
        self.assertEquals(self.resModelProgram.creator.username, 'user1')

        # # there should be a type element
        self.assertNotEqual(self.resModelProgram.metadata.type, None)

        # there should be an identifier element
        self.assertEquals(self.resModelProgram.metadata.identifiers.count(), 1)

        # there should be rights element
        self.assertNotEqual(self.resModelProgram.metadata.rights, None)

        # there shouldn't any source element
        self.assertEquals(self.resModelProgram.metadata.sources.count(), 0)

        # there shouldn't any relation element
        self.assertEquals(self.resModelProgram.metadata.relations.count(), 0)

        # there shouldn't any abstract element
        self.assertEquals(self.resModelProgram.metadata.description, None)

        # there shouldn't any coverage element
        self.assertEquals(self.resModelProgram.metadata.coverages.all().count(), 0)

        # there shouldn't any format element
        self.assertEquals(self.resModelProgram.metadata.formats.all().count(), 0)

        # there shouldn't any subject element
        self.assertEquals(self.resModelProgram.metadata.subjects.all().count(), 0)

        # there shouldn't any contributor element
        self.assertEquals(self.resModelProgram.metadata.contributors.all().count(), 0)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resModelProgram.metadata.program, None)

        # create Model program metadata
        release_date = '2016-10-24 21:05:00.315907+00:00'
        self.resModelProgram.metadata.create_element('MpMetadata',
                                                     modelVersion='5.1.011',
                                                     modelProgramLanguage='Fortran',
                                                     modelOperatingSystem='Windows',
                                                     modelReleaseDate=release_date,
                                                     modelWebsite='http://www.hydroshare.org',
                                                     modelCodeRepository='http://www.github.com',
                                                     modelReleaseNotes='releaseNote.pdf',
                                                     modelDocumentation='manual.pdf',
                                                     modelSoftware='utilities.exe',
                                                     modelEngine='sourceCode.zip')
        modelparam_element = self.resModelProgram.metadata.program
        self.assertNotEqual(modelparam_element, None)
        self.assertEqual(modelparam_element.modelVersion, '5.1.011')
        self.assertEqual(modelparam_element.modelProgramLanguage, 'Fortran')
        self.assertEqual(modelparam_element.modelOperatingSystem, 'Windows')
        self.assertEqual(str(modelparam_element.modelReleaseDate), release_date)
        self.assertEqual(modelparam_element.modelWebsite, 'http://www.hydroshare.org')
        self.assertEqual(modelparam_element.modelCodeRepository, 'http://www.github.com')
        self.assertEqual(modelparam_element.modelReleaseNotes, 'releaseNote.pdf')
        self.assertEqual(modelparam_element.modelDocumentation, 'manual.pdf')
        self.assertEqual(modelparam_element.modelSoftware, 'utilities.exe')
        self.assertEqual(modelparam_element.modelEngine, 'sourceCode.zip')

        # update Model program metadata
        release_date = '2015-10-24 21:05:00.315907+00:00'
        self.resModelProgram.metadata.update_element('MpMetadata',
                                                     self.resModelProgram.metadata.program.id,
                                                     modelVersion='1.0',
                                                     modelProgramLanguage='C',
                                                     modelOperatingSystem='Mac',
                                                     modelReleaseDate=release_date,
                                                     modelWebsite='http://dev.hydroshare.org',
                                                     modelCodeRepository='http://hydroshare.org',
                                                     modelReleaseNotes='releaseNote_1.pdf',
                                                     modelDocumentation='manual_1.pdf',
                                                     modelSoftware='utilities_1.exe',
                                                     modelEngine='sourceCode_1.zip')
        modelparam_element = self.resModelProgram.metadata.program
        self.assertNotEqual(modelparam_element, None)
        self.assertEqual(modelparam_element.modelVersion, '1.0')
        self.assertEqual(modelparam_element.modelProgramLanguage, 'C')
        self.assertEqual(modelparam_element.modelOperatingSystem, 'Mac')
        self.assertEqual(str(modelparam_element.modelReleaseDate), release_date)
        self.assertEqual(modelparam_element.modelWebsite, 'http://dev.hydroshare.org')
        self.assertEqual(modelparam_element.modelCodeRepository, 'http://hydroshare.org')
        self.assertEqual(modelparam_element.modelReleaseNotes, 'releaseNote_1.pdf')
        self.assertEqual(modelparam_element.modelDocumentation, 'manual_1.pdf')
        self.assertEqual(modelparam_element.modelSoftware, 'utilities_1.exe')
        self.assertEqual(modelparam_element.modelEngine, 'sourceCode_1.zip')

        # delete
        # check that there are all extended metadata elements at this point
        self.assertNotEqual(self.resModelProgram.metadata.program, None)

        # delete all elements
        self.resModelProgram.metadata.delete_element('MpMetadata',
                                                     self.resModelProgram.metadata.program.id)

        # make sure they are deleted
        self.assertEqual(self.resModelProgram.metadata.program, None)

    def test_public_or_discoverable(self):
        self.assertFalse(self.resModelProgram.has_required_content_files())
        self.assertFalse(self.resModelProgram.metadata.has_all_required_elements())
        self.assertFalse(self.resModelProgram.can_be_public_or_discoverable)

        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resModelProgram, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resModelProgram, files=files,
                                        user=self.user, extract_metadata=False)

        self.assertFalse(self.resModelProgram.can_be_public_or_discoverable)

        self.resModelProgram.metadata.create_element('Description', abstract="test abstract")
        self.assertFalse(self.resModelProgram.can_be_public_or_discoverable)

        self.resModelProgram.metadata.create_element('Subject', value="test subject")

        self.assertTrue(self.resModelProgram.has_required_content_files())
        self.assertTrue(self.resModelProgram.metadata.has_all_required_elements())
        self.assertTrue(self.resModelProgram.can_be_public_or_discoverable)

    def test_can_have_multiple_content_files(self):
        self.assertTrue(ModelProgramResource.can_have_multiple_files())

    def test_can_upload_multiple_content_files(self):
        # more than one file can be uploaded
        self.assertTrue(ModelProgramResource.allow_multiple_file_upload())

    def test_get_xml(self):
        self.resModelProgram.metadata.create_element('Description', abstract="test abstract")
        self.resModelProgram.metadata.create_element('Subject', value="test subject")
        release_date = '2016-10-24T21:05:00.315907+00:00'
        self.resModelProgram.metadata.create_element('MpMetadata',
                                                     modelVersion='5.1.011',
                                                     modelProgramLanguage='Fortran',
                                                     modelOperatingSystem='Windows',
                                                     modelReleaseDate=release_date,
                                                     modelWebsite='http://www.hydroshare.org',
                                                     modelCodeRepository='http://www.github.com',
                                                     modelReleaseNotes='releaseNote.pdf',
                                                     modelDocumentation='manual.pdf',
                                                     modelSoftware='utilities.exe',
                                                     modelEngine='sourceCode.zip')

        # test if xml from get_xml() is well formed
        ET.fromstring(self.resModelProgram.metadata.get_xml())
        xml_doc = self.resModelProgram.metadata.get_xml()
        # check to see if the specific metadata are in the xml doc
        self.assertTrue('5.1.011' in xml_doc)
        self.assertTrue('Fortran' in xml_doc)
        self.assertTrue('Windows' in xml_doc)
        self.assertTrue(release_date in xml_doc)
        self.assertTrue('http://www.hydroshare.org' in xml_doc)
        self.assertTrue('http://www.github.com' in xml_doc)
        self.assertTrue('releaseNote.pdf' in xml_doc)
        self.assertTrue('manual.pdf' in xml_doc)
        self.assertTrue('utilities.exe' in xml_doc)
        self.assertTrue('sourceCode.zip' in xml_doc)

    def test_metadata_on_content_file_delete(self):
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resModelProgram, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resModelProgram, files=files,
                                        user=self.user, extract_metadata=False)

        self.resModelProgram.metadata.create_element('Description', abstract="test abstract")
        self.resModelProgram.metadata.create_element('Subject', value="test subject")
        release_date = '2016-10-24T21:05:00.315907+00:00'
        self.resModelProgram.metadata.create_element('MpMetadata',
                                                     modelVersion='5.1.011',
                                                     modelProgramLanguage='Fortran',
                                                     modelOperatingSystem='Windows',
                                                     modelReleaseDate=release_date,
                                                     modelWebsite='http://www.hydroshare.org',
                                                     modelCodeRepository='http://www.github.com',
                                                     modelReleaseNotes='releaseNote.pdf',
                                                     modelDocumentation='manual.pdf',
                                                     modelSoftware='utilities.exe',
                                                     modelEngine='sourceCode.zip')

        # there should one content file
        self.assertEquals(self.resModelProgram.files.all().count(), 1)

        # there should be one format element
        self.assertEquals(self.resModelProgram.metadata.formats.all().count(), 1)

        # the short path should just consist of the file name.
        self.assertEquals(self.resModelProgram.files.all()[0].short_path, self.file_name)

        # delete content file that we added above; note that file name is a short_path
        hydroshare.delete_resource_file(self.resModelProgram.short_id, self.file_name, self.user)

        # there should no content file
        self.assertEquals(self.resModelProgram.files.all().count(), 0)

        # test the core metadata at this point
        self.assertNotEquals(self.resModelProgram.metadata.title, None)

        # there should be an abstract element
        self.assertNotEquals(self.resModelProgram.metadata.description, None)

        # there should be one creator element
        self.assertEquals(self.resModelProgram.metadata.creators.all().count(), 1)

        # testing extended metadata elements
        self.assertNotEqual(self.resModelProgram.metadata.program, None)

    def test_metadata_delete_on_resource_delete(self):
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resModelProgram, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resModelProgram, files=files,
                                        user=self.user, extract_metadata=False)

        self.resModelProgram.metadata.create_element('Description', abstract="test abstract")
        self.resModelProgram.metadata.create_element('Subject', value="test subject")
        release_date = '2016-10-24T21:05:00.315907+00:00'
        self.resModelProgram.metadata.create_element('MpMetadata',
                                                     modelVersion='5.1.011',
                                                     modelProgramLanguage='Fortran',
                                                     modelOperatingSystem='Windows',
                                                     modelReleaseDate=release_date,
                                                     modelWebsite='http://www.hydroshare.org',
                                                     modelCodeRepository='http://www.github.com',
                                                     modelReleaseNotes='releaseNote.pdf',
                                                     modelDocumentation='manual.pdf',
                                                     modelSoftware='utilities.exe',
                                                     modelEngine='sourceCode.zip')
        self.resModelProgram.metadata.create_element('Contributor', name="user2")

        # before resource delete
        core_metadata_obj = self.resModelProgram.metadata
        self.assertEqual(CoreMetaData.objects.all().count(), 1)
        # there should be Creator metadata objects
        self.assertTrue(Creator.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Contributor metadata objects
        self.assertTrue(Contributor.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Identifier metadata objects
        self.assertTrue(Identifier.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Type metadata objects
        self.assertTrue(Type.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Source metadata objects
        self.assertFalse(Source.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Relation metadata objects
        self.assertFalse(Relation.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Publisher metadata objects
        self.assertFalse(Publisher.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Title metadata objects
        self.assertTrue(Title.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Description (Abstract) metadata objects
        self.assertTrue(Description.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Date metadata objects
        self.assertTrue(Date.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Subject metadata objects
        self.assertTrue(Subject.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Coverage metadata objects
        self.assertFalse(Coverage.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Format metadata objects
        self.assertTrue(Format.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Language metadata objects
        self.assertTrue(Language.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Rights metadata objects
        self.assertTrue(Rights.objects.filter(object_id=core_metadata_obj.id).exists())

        # resource specific metadata
        # there should be Model Program metadata objects
        self.assertTrue(MpMetadata.objects.filter(object_id=core_metadata_obj.id).exists())

        # delete resource
        hydroshare.delete_resource(self.resModelProgram.short_id)
        self.assertEquals(CoreMetaData.objects.all().count(), 0)

        # there should be no Creator metadata objects
        self.assertFalse(Creator.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Contributor metadata objects
        self.assertFalse(Contributor.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Identifier metadata objects
        self.assertFalse(Identifier.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Type metadata objects
        self.assertFalse(Type.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Source metadata objects
        self.assertFalse(Source.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Relation metadata objects
        self.assertFalse(Relation.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Publisher metadata objects
        self.assertFalse(Publisher.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Title metadata objects
        self.assertFalse(Title.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Description (Abstract) metadata objects
        self.assertFalse(Description.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Date metadata objects
        self.assertFalse(Date.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Subject metadata objects
        self.assertFalse(Subject.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Coverage metadata objects
        self.assertFalse(Coverage.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Format metadata objects
        self.assertFalse(Format.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Language metadata objects
        self.assertFalse(Language.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Rights metadata objects
        self.assertFalse(Rights.objects.filter(object_id=core_metadata_obj.id).exists())

        # resource specific metadata
        # there should be no Model Output metadata objects
        self.assertFalse(MpMetadata.objects.filter(object_id=core_metadata_obj.id).exists())
