import os
import tempfile
import shutil
from dateutil import parser

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

        self.temp_dir = tempfile.mkdtemp()
        temp_text_file = os.path.join(self.temp_dir, 'MIR.txt')
        text_file = open(temp_text_file, 'w')
        text_file.write("Model Instance resource files")
        self.text_file_obj = open(temp_text_file, 'r')

    def tearDown(self):
        super(TestModelInstanceMetaData, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_allowed_file_types(self):
        # test allowed file type is '.*'
        self.assertIn('.*', ModelInstanceResource.get_supported_upload_file_types())
        self.assertEquals(len(ModelInstanceResource.get_supported_upload_file_types()), 2)

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

    #def test_metadata_on_content_file_delete(self):


    def test_extended_metadata_CRUD(self):
          # test the core metadata at this point
        self.assertEquals(self.resModelInstance.metadata.title.value, 'Test Model Instance Resource')

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
        self.assertEquals(self.resModelInstance.metadata.model_output,None)
        self.assertEquals(self.resModelInstance.metadata.executed_by, None)

        # create
        self.resModelInstance.metadata.create_element('ModelOutput')

        ModelOutput_element = self.resModelInstance.metadata.model_output
        self.assertEquals(ModelOutput_element.includes_output, False)

        # multiple ModelOutput elements are not allowed - should raise exception
        with self.assertRaises(IntegrityError):
            self.resModelInstance.metadata.create_element('ModelOutput', includes_output= True)

        self.resModelInstance.metadata.create_element('ExecutedBy', model_name= self.resModelProgram.short_id)

        ExecutedBy_element = self.resModelInstance.metadata.executed_by
        self.assertEquals(ExecutedBy_element.model_name, "Model Program Resource")
