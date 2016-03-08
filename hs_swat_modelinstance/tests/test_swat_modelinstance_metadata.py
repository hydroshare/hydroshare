import os
import tempfile
import shutil

from xml.etree import ElementTree as ET

from django.test import TransactionTestCase
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.models import Group
from django.db import IntegrityError, ValidationError

from hs_core import hydroshare
from hs_core.hydroshare import utils
from hs_core.models import CoreMetaData, Creator, Contributor, Coverage, Rights, Title, Language, \
    Publisher, Identifier, Type, Subject, Description, Date, Format, Relation, Source
from hs_core.testing import MockIRODSTestCaseMixin
from hs_swat_modelinstance.models import SWATModelInstanceResource, \
    SWATModelInstanceMetaData, \
    ModelObjectiveChoices, \
    ModelObjective,\
    ModelMethod,\
    ModelParameter,\
    ModelParametersChoices,\
    ModelInput


class TestSWATModelInstanceMetaData(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TestSWATModelInstanceMetaData, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.resSWATModelInstance = hydroshare.create_resource(
            resource_type='SWATModelInstanceResource',
            owner=self.user,
            title='Test SWAT Model Instance Resource'
        )

        self.resGenModelProgram = hydroshare.create_resource(
            resource_type='ModelProgramResource',
            owner=self.user,
            title='Model SWAT Program Resource'
        )

        self.resSwatModelProgram = hydroshare.create_resource(
            resource_type='ModelProgramResource',
            owner=self.user,
            title='Model Program Resource 2'
        )

        self.temp_dir = tempfile.mkdtemp()
        self.file_name = "MIR.txt"
        temp_text_file = os.path.join(self.temp_dir, self.file_name)
        text_file = open(temp_text_file, 'w')
        text_file.write("Model SWAT Instance resource files")
        self.text_file_obj = open(temp_text_file, 'r')

    def tearDown(self):
        super(TestSWATModelInstanceMetaData, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_allowed_file_types(self):
        # test allowed file type is '.*'        
        self.assertEquals(self.resSWATModelInstance.get_supported_upload_file_types(), '.*')

        # there should not be any content file
        self.assertEquals(self.resSWATModelInstance.files.all().count(), 0)

        # Upload any file type should pass both the file pre add check post add check
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resSWATModelInstance, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resSWATModelInstance, files=files, user=self.user,
                                        extract_metadata=False)

        # there should one content file
        self.assertEquals(self.resSWATModelInstance.files.all().count(), 1)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resSWATModelInstance.metadata.model_output, None)
        self.assertEquals(self.resSWATModelInstance.metadata.executed_by, None)

        # Upload any other file type should pass both the file pre add check post add check
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resSWATModelInstance, files=files, user=self.user,
                                            extract_metadata=True)

        utils.resource_file_add_process(resource=self.resSWATModelInstance, files=files, user=self.user,
                                        extract_metadata=True)

        # there should two content files
        self.assertEquals(self.resSWATModelInstance.files.all().count(), 2)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resSWATModelInstance.metadata.model_output, None)
        self.assertEquals(self.resSWATModelInstance.metadata.executed_by, None)

    def test_extended_metadata_CRUD(self):
        # test the core metadata at this point
        # there should be a title element
        self.assertEquals(self.resSWATModelInstance.metadata.title.value, 'Test SWAT Model Instance Resource')

        # there should be a creator element
        self.assertEquals(self.resSWATModelInstance.creator.username, 'user1')

        # # there should be a type element
        self.assertNotEqual(self.resSWATModelInstance.metadata.type, None)

        # there should be an identifier element
        self.assertEquals(self.resSWATModelInstance.metadata.identifiers.count(), 1)

        # there should be rights element
        self.assertNotEqual(self.resSWATModelInstance.metadata.rights, None)

        # there shouldn't any source element
        self.assertEquals(self.resSWATModelInstance.metadata.sources.count(), 0)

        # there shouldn't any relation element
        self.assertEquals(self.resSWATModelInstance.metadata.relations.count(), 0)

        # there shouldn't any abstract element
        self.assertEquals(self.resSWATModelInstance.metadata.description, None)

        # there shouldn't any coverage element
        self.assertEquals(self.resSWATModelInstance.metadata.coverages.all().count(), 0)

        # there shouldn't any format element
        self.assertEquals(self.resSWATModelInstance.metadata.formats.all().count(), 0)

        # there shouldn't any subject element
        self.assertEquals(self.resSWATModelInstance.metadata.subjects.all().count(), 0)

        # there shouldn't any contributor element
        self.assertEquals(self.resSWATModelInstance.metadata.contributors.all().count(), 0)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resSWATModelInstance.metadata.model_output, None)
        self.assertEquals(self.resSWATModelInstance.metadata.executed_by, None)
        self.assertEquals(self.resSWATModelInstance.metadata.ModelInput, None)
        self.assertEquals(self.resSWATModelInstance.metadata.ModelParameter, None)
        self.assertEquals(self.resSWATModelInstance.metadata.ModelMethod, None)
        self.assertEquals(self.resSWATModelInstance.metadata.SimulationType, None)
        self.assertEquals(self.resSWATModelInstance.metadata.ModelObjective, None)

        #create
        # create model_output
        self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=False)

        modeloutput_element = self.resSWATModelInstance.metadata.model_output
        self.assertEquals(modeloutput_element.includes_output, False)

        # multiple ModelOutput elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=True)

        with self.assertRaises(IntegrityError):
            self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=False)

        self.resSWATModelInstance.metadata.delete_element('ModelOutput', self.resSWATModelInstance.metadata.model_output.id)

        self.assertEqual(self.resSWATModelInstance.metadata.model_output, None)

        self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=True)

        modeloutput_element = self.resSWATModelInstance.metadata.model_output
        self.assertEquals(modeloutput_element.includes_output, True)

        # multiple ModelOutput elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=True)

        with self.assertRaises(IntegrityError):
            self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=False)


        # create ExecutedBy
        self.resSWATModelInstance.metadata.create_element('ExecutedBy', model_name=self.resGenModelProgram.short_id)

        modelobjective_element = self.resSWATModelInstance.metadata.executed_by
        self.assertEquals(modelobjective_element.model_name, self.resGenModelProgram.metadata.title.value)
        self.assertEquals(modelobjective_element.model_program_fk, self.resGenModelProgram)

        # multiple ExecutedBy elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resSWATModelInstance.metadata.create_element('ExecutedBy', model_name=self.resSwatModelProgram.short_id)


        # create ModelObjective
        s_objectives = ["BMPs", "Hydrology"]
        o_obj = "elon musk"
        self.resSWATModelInstance.metadata.create_element('ModelObjective',
                                                          swat_model_objectives={s_objectives[0]: s_objectives[0],
                                                                                 s_objectives[1]: s_objectives[1]},
                                                          other_objectives=o_obj)

        modelobjective_element = self.resSWATModelInstance.metadata.model_objective
        v = modelobjective_element.swat_model_objectives.values
        val_list = [d['description'] for d in v]
        for o in s_objectives:
            self.assertEquals(o in val_list, True)
        self.assertEquals(modelobjective_element.other_objectives, o_obj)

        # try to create a swat_model_objective with a non cv term
        with self.assertRaises(ValidationError):
            self.resSWATModelInstance.metadata.create_element('ModelObjective',
                                                              swat_model_objectives={"gravity waves":"gravity waves"})


    #     # update
    #     self.resSWATModelInstance.metadata.update_element('ModelOutput', self.resSWATModelInstance.metadata.model_output.id,
    #                                                       includes_output=False)
    #
    #     self.assertEquals(self.resSWATModelInstance.metadata.model_output.includes_output, False)
    #
    #     self.resSWATModelInstance.metadata.update_element('ModelOutput', self.resSWATModelInstance.metadata.model_output.id,
    #                                                       includes_output=True)
    #
    #     self.assertEquals(self.resSWATModelInstance.metadata.model_output.includes_output, True)
    #
    #     self.resSWATModelInstance.metadata.update_element('ExecutedBy', self.resSWATModelInstance.metadata.executed_by.id,
    #                                                       model_name=self.resSwatModelProgram.short_id)
    #
    #     modelobjective_element = self.resSWATModelInstance.metadata.executed_by
    #     self.assertEquals(modelobjective_element.model_name, self.resSwatModelProgram.metadata.title.value)
    #     self.assertEquals(modelobjective_element.model_program_fk, self.resSwatModelProgram)
    #
    #     # delete
    #     self.assertNotEqual(self.resSWATModelInstance.metadata.model_output, None)
    #     self.assertNotEqual(self.resSWATModelInstance.metadata.executed_by, None)
    #
    #     self.resSWATModelInstance.metadata.delete_element('ModelOutput', self.resSWATModelInstance.metadata.model_output.id)
    #     self.resSWATModelInstance.metadata.delete_element('ExecutedBy', self.resSWATModelInstance.metadata.executed_by.id)
    #
    #     self.assertEqual(self.resSWATModelInstance.metadata.model_output, None)
    #     self.assertEqual(self.resSWATModelInstance.metadata.executed_by, None)
    #
    # def test_public_or_discoverable(self):
    #     self.assertFalse(self.resSWATModelInstance.has_required_content_files())
    #     self.assertFalse(self.resSWATModelInstance.metadata.has_all_required_elements())
    #     self.assertFalse(self.resSWATModelInstance.can_be_public_or_discoverable)
    #
    #     files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
    #     utils.resource_file_add_pre_process(resource=self.resSWATModelInstance, files=files, user=self.user,
    #                                         extract_metadata=False)
    #
    #     utils.resource_file_add_process(resource=self.resSWATModelInstance, files=files, user=self.user,
    #                                     extract_metadata=False)
    #
    #     self.assertFalse(self.resSWATModelInstance.can_be_public_or_discoverable)
    #
    #     self.resSWATModelInstance.metadata.create_element('Description', abstract="test abstract")
    #     self.assertFalse(self.resSWATModelInstance.can_be_public_or_discoverable)
    #
    #     self.resSWATModelInstance.metadata.create_element('Subject', value="test subject")
    #
    #     self.assertTrue(self.resSWATModelInstance.has_required_content_files())
    #     self.assertTrue(self.resSWATModelInstance.metadata.has_all_required_elements())
    #     self.assertTrue(self.resSWATModelInstance.can_be_public_or_discoverable)
    #
    # def test_multiple_content_files(self):
    #     self.assertTrue(ModelInstanceResource.can_have_multiple_files())
    #
    # def test_get_xml(self):
    #     self.resSWATModelInstance.metadata.create_element('Description', abstract="test abstract")
    #     self.resSWATModelInstance.metadata.create_element('Subject', value="test subject")
    #     self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=True)
    #     self.resSWATModelInstance.metadata.create_element('ExecutedBy', model_name=self.resGenModelProgram.short_id)
    #
    #     # test if xml from get_xml() is well formed
    #     ET.fromstring(self.resSWATModelInstance.metadata.get_xml())
    #
    # def test_metadata_on_content_file_delete(self):
    #     files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
    #     utils.resource_file_add_pre_process(resource=self.resSWATModelInstance, files=files, user=self.user,
    #                                         extract_metadata=False)
    #
    #     utils.resource_file_add_process(resource=self.resSWATModelInstance, files=files, user=self.user,
    #                                     extract_metadata=False)
    #
    #     self.resSWATModelInstance.metadata.create_element('Description', abstract="test abstract")
    #     self.resSWATModelInstance.metadata.create_element('Subject', value="test subject")
    #     self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=True)
    #     self.resSWATModelInstance.metadata.create_element('ExecutedBy', model_name=self.resGenModelProgram.short_id)
    #
    #     # there should one content file
    #     self.assertEquals(self.resSWATModelInstance.files.all().count(), 1)
    #
    #     # there should be one format element
    #     self.assertEquals(self.resSWATModelInstance.metadata.formats.all().count(), 1)
    #
    #     # delete content file that we added above
    #     hydroshare.delete_resource_file(self.resSWATModelInstance.short_id, self.file_name, self.user)
    #     # there should no content file
    #     self.assertEquals(self.resSWATModelInstance.files.all().count(), 0)
    #
    #     # test the core metadata at this point
    #     self.assertNotEquals(self.resSWATModelInstance.metadata.title, None)
    #
    #     # there should be an abstract element
    #     self.assertNotEquals(self.resSWATModelInstance.metadata.description, None)
    #
    #     # there should be one creator element
    #     self.assertEquals(self.resSWATModelInstance.metadata.creators.all().count(), 1)
    #
    #     # testing extended metadata elements
    #     self.assertNotEqual(self.resSWATModelInstance.metadata.model_output, None)
    #     self.assertNotEqual(self.resSWATModelInstance.metadata.executed_by, None)
    #
    # def test_metadata_delete_on_resource_delete(self):
    #     files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
    #     utils.resource_file_add_pre_process(resource=self.resSWATModelInstance, files=files, user=self.user,
    #                                         extract_metadata=False)
    #
    #     utils.resource_file_add_process(resource=self.resSWATModelInstance, files=files, user=self.user,
    #                                     extract_metadata=False)
    #
    #     self.resSWATModelInstance.metadata.create_element('Description', abstract="test abstract")
    #     self.resSWATModelInstance.metadata.create_element('Subject', value="test subject")
    #     self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=True)
    #     self.resSWATModelInstance.metadata.create_element('ExecutedBy', model_name=self.resGenModelProgram.short_id)
    #     self.resSWATModelInstance.metadata.create_element('Contributor', name="user2")
    #
    #     # before resource delete
    #     core_metadata_obj = self.resSWATModelInstance.metadata
    #     self.assertEquals(CoreMetaData.objects.all().count(), 3)
    #     # there should be Creator metadata objects
    #     self.assertTrue(Creator.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Contributor metadata objects
    #     self.assertTrue(Contributor.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Identifier metadata objects
    #     self.assertTrue(Identifier.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Type metadata objects
    #     self.assertTrue(Type.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Source metadata objects
    #     self.assertFalse(Source.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Relation metadata objects
    #     self.assertFalse(Relation.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Publisher metadata objects
    #     self.assertFalse(Publisher.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Title metadata objects
    #     self.assertTrue(Title.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Description (Abstract) metadata objects
    #     self.assertTrue(Description.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Date metadata objects
    #     self.assertTrue(Date.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Subject metadata objects
    #     self.assertTrue(Subject.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Coverage metadata objects
    #     self.assertFalse(Coverage.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Format metadata objects
    #     self.assertTrue(Format.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Language metadata objects
    #     self.assertTrue(Language.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Rights metadata objects
    #     self.assertTrue(Rights.objects.filter(object_id=core_metadata_obj.id).exists())
    #
    #     # resource specific metadata
    #     # there should be Model Output metadata objects
    #     self.assertTrue(ModelOutput.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be ExecutedBy metadata objects
    #     self.assertTrue(ExecutedBy.objects.filter(object_id=core_metadata_obj.id).exists())
    #
    #     # delete resource
    #     hydroshare.delete_resource(self.resSWATModelInstance.short_id)
    #     self.assertEquals(CoreMetaData.objects.all().count(), 2)
    #
    #     # there should be no Creator metadata objects
    #     self.assertFalse(Creator.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Contributor metadata objects
    #     self.assertFalse(Contributor.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Identifier metadata objects
    #     self.assertFalse(Identifier.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Type metadata objects
    #     self.assertFalse(Type.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Source metadata objects
    #     self.assertFalse(Source.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Relation metadata objects
    #     self.assertFalse(Relation.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Publisher metadata objects
    #     self.assertFalse(Publisher.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Title metadata objects
    #     self.assertFalse(Title.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Description (Abstract) metadata objects
    #     self.assertFalse(Description.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Date metadata objects
    #     self.assertFalse(Date.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Subject metadata objects
    #     self.assertFalse(Subject.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Coverage metadata objects
    #     self.assertFalse(Coverage.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Format metadata objects
    #     self.assertFalse(Format.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Language metadata objects
    #     self.assertFalse(Language.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Rights metadata objects
    #     self.assertFalse(Rights.objects.filter(object_id=core_metadata_obj.id).exists())
    #
    #     # resource specific metadata
    #     # there should be no Model Output metadata objects
    #     self.assertFalse(ModelOutput.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no ExecutedBy metadata objects
    #     self.assertFalse(ExecutedBy.objects.filter(object_id=core_metadata_obj.id).exists())
