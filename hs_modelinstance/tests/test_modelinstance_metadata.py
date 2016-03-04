import os
import tempfile
import shutil

from xml.etree import ElementTree as ET

from django.test import TransactionTestCase
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.models import Group
from django.db import IntegrityError

from hs_core import hydroshare
from hs_core.hydroshare import utils
from hs_core.models import CoreMetaData, Creator, Contributor, Coverage, Rights, Title, Language, \
    Publisher, Identifier, Type, Subject, Description, Date, Format, Relation, Source
from hs_core.testing import MockIRODSTestCaseMixin
from hs_modelinstance.models import ModelInstanceResource, ModelOutput, ExecutedBy


class TestModelInstanceMetaData(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TestModelInstanceMetaData, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.resModelInstance = hydroshare.create_resource(
            resource_type='ModelInstanceResource',
            owner=self.user,
            title='Test Model Instance Resource'
        )

        self.resModelProgram = hydroshare.create_resource(
            resource_type='ModelProgramResource',
            owner=self.user,
            title='Model Program Resource'
        )

        self.resModelProgram2 = hydroshare.create_resource(
            resource_type='ModelProgramResource',
            owner=self.user,
            title='Model Program Resource 2'
        )

        self.temp_dir = tempfile.mkdtemp()
        self.file_name = "MIR.txt"
        temp_text_file = os.path.join(self.temp_dir, self.file_name)
        text_file = open(temp_text_file, 'w')
        text_file.write("Model Instance resource files")
        self.text_file_obj = open(temp_text_file, 'r')

    def tearDown(self):
        super(TestModelInstanceMetaData, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_allowed_file_types(self):
        # test allowed file type is '.*'        
        self.assertEquals(self.resModelInstance.get_supported_upload_file_types(), '.*')

        # there should not be any content file
        self.assertEquals(self.resModelInstance.files.all().count(), 0)

        # Upload any file type should pass both the file pre add check post add check
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resModelInstance, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resModelInstance, files=files, user=self.user,
                                        extract_metadata=False)

        # there should one content file
        self.assertEquals(self.resModelInstance.files.all().count(), 1)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resModelInstance.metadata.model_output, None)
        self.assertEquals(self.resModelInstance.metadata.executed_by, None)

        # Upload any other file type should pass both the file pre add check post add check
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resModelInstance, files=files, user=self.user,
                                            extract_metadata=True)

        utils.resource_file_add_process(resource=self.resModelInstance, files=files, user=self.user,
                                        extract_metadata=True)

        # there should two content files
        self.assertEquals(self.resModelInstance.files.all().count(), 2)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resModelInstance.metadata.model_output, None)
        self.assertEquals(self.resModelInstance.metadata.executed_by, None)

    def test_extended_metadata_CRUD(self):
        # test the core metadata at this point
        # there should be a title element
        self.assertEquals(self.resModelInstance.metadata.title.value, 'Test Model Instance Resource')

        # there should be a creator element
        self.assertEquals(self.resModelInstance.creator.username, 'user1')

        # # there should be a type element
        self.assertNotEqual(self.resModelInstance.metadata.type, None)

        # there should be an identifier element
        self.assertEquals(self.resModelInstance.metadata.identifiers.count(), 1)

        # there should be rights element
        self.assertNotEqual(self.resModelInstance.metadata.rights, None)

        # there shouldn't any source element
        self.assertEquals(self.resModelInstance.metadata.sources.count(), 0)

        # there shouldn't any relation element
        self.assertEquals(self.resModelInstance.metadata.relations.count(), 0)

        # there shouldn't any abstract element
        self.assertEquals(self.resModelInstance.metadata.description, None)

        # there shouldn't any coverage element
        self.assertEquals(self.resModelInstance.metadata.coverages.all().count(), 0)

        # there shouldn't any format element
        self.assertEquals(self.resModelInstance.metadata.formats.all().count(), 0)

        # there shouldn't any subject element
        self.assertEquals(self.resModelInstance.metadata.subjects.all().count(), 0)

        # there shouldn't any contributor element
        self.assertEquals(self.resModelInstance.metadata.contributors.all().count(), 0)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resModelInstance.metadata.model_output, None)
        self.assertEquals(self.resModelInstance.metadata.executed_by, None)

        # create
        self.resModelInstance.metadata.create_element('ModelOutput', includes_output=False)

        modeloutput_element = self.resModelInstance.metadata.model_output
        self.assertEquals(modeloutput_element.includes_output, False)

        # multiple ModelOutput elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resModelInstance.metadata.create_element('ModelOutput', includes_output=True)

        with self.assertRaises(IntegrityError):
            self.resModelInstance.metadata.create_element('ModelOutput', includes_output=False)

        self.resModelInstance.metadata.delete_element('ModelOutput', self.resModelInstance.metadata.model_output.id)

        self.assertEqual(self.resModelInstance.metadata.model_output, None)

        self.resModelInstance.metadata.create_element('ModelOutput', includes_output=True)

        modeloutput_element = self.resModelInstance.metadata.model_output
        self.assertEquals(modeloutput_element.includes_output, True)

        # multiple ModelOutput elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resModelInstance.metadata.create_element('ModelOutput', includes_output=True)

        with self.assertRaises(IntegrityError):
            self.resModelInstance.metadata.create_element('ModelOutput', includes_output=False)


        self.resModelInstance.metadata.create_element('ExecutedBy', model_name=self.resModelProgram.short_id)

        executedby_element = self.resModelInstance.metadata.executed_by
        self.assertEquals(executedby_element.model_name, self.resModelProgram.metadata.title.value)
        self.assertEquals(executedby_element.model_program_fk, self.resModelProgram)

        # multiple ExecutedBy elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resModelInstance.metadata.create_element('ExecutedBy', model_name=self.resModelProgram2.short_id)

        # update
        self.resModelInstance.metadata.update_element('ModelOutput', self.resModelInstance.metadata.model_output.id,
                                                      includes_output=False)

        self.assertEquals(self.resModelInstance.metadata.model_output.includes_output, False)

        self.resModelInstance.metadata.update_element('ModelOutput', self.resModelInstance.metadata.model_output.id,
                                                      includes_output=True)

        self.assertEquals(self.resModelInstance.metadata.model_output.includes_output, True)

        self.resModelInstance.metadata.update_element('ExecutedBy', self.resModelInstance.metadata.executed_by.id,
                                                      model_name=self.resModelProgram2.short_id)

        executedby_element = self.resModelInstance.metadata.executed_by
        self.assertEquals(executedby_element.model_name, self.resModelProgram2.metadata.title.value)
        self.assertEquals(executedby_element.model_program_fk, self.resModelProgram2)

        # delete
        self.assertNotEqual(self.resModelInstance.metadata.model_output, None)
        self.assertNotEqual(self.resModelInstance.metadata.executed_by, None)

        self.resModelInstance.metadata.delete_element('ModelOutput', self.resModelInstance.metadata.model_output.id)
        self.resModelInstance.metadata.delete_element('ExecutedBy', self.resModelInstance.metadata.executed_by.id)

        self.assertEqual(self.resModelInstance.metadata.model_output, None)
        self.assertEqual(self.resModelInstance.metadata.executed_by, None)
        
    def test_public_or_discoverable(self):
        self.assertFalse(self.resModelInstance.has_required_content_files())
        self.assertFalse(self.resModelInstance.metadata.has_all_required_elements())
        self.assertFalse(self.resModelInstance.can_be_public_or_discoverable)

        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resModelInstance, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resModelInstance, files=files, user=self.user,
                                        extract_metadata=False)

        self.assertFalse(self.resModelInstance.can_be_public_or_discoverable)

        self.resModelInstance.metadata.create_element('Description', abstract="test abstract")
        self.assertFalse(self.resModelInstance.can_be_public_or_discoverable)

        self.resModelInstance.metadata.create_element('Subject', value="test subject")

        self.assertTrue(self.resModelInstance.has_required_content_files())
        self.assertTrue(self.resModelInstance.metadata.has_all_required_elements())
        self.assertTrue(self.resModelInstance.can_be_public_or_discoverable)

    def test_multiple_content_files(self):
        self.assertTrue(ModelInstanceResource.can_have_multiple_files())

    def test_get_xml(self):
        self.resModelInstance.metadata.create_element('Description', abstract="test abstract")
        self.resModelInstance.metadata.create_element('Subject', value="test subject")
        self.resModelInstance.metadata.create_element('ModelOutput', includes_output=True)
        self.resModelInstance.metadata.create_element('ExecutedBy', model_name=self.resModelProgram.short_id)

        # test if xml from get_xml() is well formed
        ET.fromstring(self.resModelInstance.metadata.get_xml())

    def test_metadata_on_content_file_delete(self):
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resModelInstance, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resModelInstance, files=files, user=self.user,
                                        extract_metadata=False)

        self.resModelInstance.metadata.create_element('Description', abstract="test abstract")
        self.resModelInstance.metadata.create_element('Subject', value="test subject")
        self.resModelInstance.metadata.create_element('ModelOutput', includes_output=True)
        self.resModelInstance.metadata.create_element('ExecutedBy', model_name=self.resModelProgram.short_id)

        # there should one content file
        self.assertEquals(self.resModelInstance.files.all().count(), 1)

        # there should be one format element
        self.assertEquals(self.resModelInstance.metadata.formats.all().count(), 1)

        # delete content file that we added above
        hydroshare.delete_resource_file(self.resModelInstance.short_id, self.file_name, self.user)
        # there should no content file
        self.assertEquals(self.resModelInstance.files.all().count(), 0)

        # test the core metadata at this point
        self.assertNotEquals(self.resModelInstance.metadata.title, None)

        # there should be an abstract element
        self.assertNotEquals(self.resModelInstance.metadata.description, None)

        # there should be one creator element
        self.assertEquals(self.resModelInstance.metadata.creators.all().count(), 1)

        # testing extended metadata elements
        self.assertNotEqual(self.resModelInstance.metadata.model_output, None)
        self.assertNotEqual(self.resModelInstance.metadata.executed_by, None)

    def test_metadata_delete_on_resource_delete(self):
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resModelInstance, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resModelInstance, files=files, user=self.user,
                                        extract_metadata=False)

        self.resModelInstance.metadata.create_element('Description', abstract="test abstract")
        self.resModelInstance.metadata.create_element('Subject', value="test subject")
        self.resModelInstance.metadata.create_element('ModelOutput', includes_output=True)
        self.resModelInstance.metadata.create_element('ExecutedBy', model_name=self.resModelProgram.short_id)
        self.resModelInstance.metadata.create_element('Contributor', name="user2")

        # before resource delete
        core_metadata_obj = self.resModelInstance.metadata
        self.assertEquals(CoreMetaData.objects.all().count(), 3)
        # there should be Creator metadata objects
        self.assertTrue(Creator.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Contributor metadata objects
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
        # there should be Model Output metadata objects
        self.assertTrue(ModelOutput.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be ExecutedBy metadata objects
        self.assertTrue(ExecutedBy.objects.filter(object_id=core_metadata_obj.id).exists())

        # delete resource
        hydroshare.delete_resource(self.resModelInstance.short_id)
        self.assertEquals(CoreMetaData.objects.all().count(), 2)

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
        self.assertFalse(ModelOutput.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no ExecutedBy metadata objects
        self.assertFalse(ExecutedBy.objects.filter(object_id=core_metadata_obj.id).exists())
