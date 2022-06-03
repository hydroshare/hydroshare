import glob
import json
import os

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from rest_framework import status

from hs_core import hydroshare
from hs_core.hydroshare import add_file_to_resource
from hs_core.models import ResourceFile
from hs_core.tests.api.rest.base import HSRESTTestCase
from hs_file_types.models import ModelInstanceLogicalFile, ModelProgramLogicalFile, ModelProgramResourceFileType


class TestModelProgramTemplateSchema(HSRESTTestCase):

    def setUp(self):
        super(TestModelProgramTemplateSchema, self).setUp()
        self.res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Testing Model Aggregation Template Related Endpoints',
            keywords=['kw1', 'kw2']
        )

        self.schema_templates = []
        template_path = settings.MODEL_PROGRAM_META_SCHEMA_TEMPLATE_PATH
        template_path = os.path.join(template_path, "*.json")
        for schema_template in glob.glob(template_path):
            template_file_name = os.path.basename(schema_template)
            self.schema_templates.append(template_file_name)

    def tearDown(self):
        super(TestModelProgramTemplateSchema, self).tearDown()
        self.res.delete()

    def test_list_template_schemas(self):
        """Test that we can get the filenames of all available metadata template schema for model program."""

        url = "/hsapi/modelprogram/template/meta/schemas/"
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content.decode())
        template_schema_filenames = set([c['meta_schema_filename'] for c in content])

        self.assertEqual(template_schema_filenames, set(self.schema_templates))
        self.assertNotEqual(len(self.schema_templates), 0)

    def test_get_template_schema(self):
        """Test that we can get the content of of any specified template metadata schema."""

        url = "/hsapi/modelprogram/template/meta/schema/{}"
        for schema_filename in self.schema_templates:
            response = self.client.get(url.format(schema_filename), format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            content = json.loads(response.content.decode())
            self.assertTrue(content)
            self.assertEqual(content['type'], 'object')

    def test_assign_template_meta_schema_to_model_program_aggr(self):
        """Test that we can assign any of the template metadata schema to a model program aggregation."""

        mp_aggr = self._create_model_program_aggregation(expected_file_count=1, upload_folder='mp-folder')
        aggr_path = mp_aggr.aggregation_name
        for template_schema_filename in self.schema_templates:
            mp_aggr = ModelProgramLogicalFile.objects.first()
            self.assertFalse(mp_aggr.metadata_schema_json)
            url = f"/hsapi/resource/{self.res.short_id}/modelprogram/template/meta/schema/{aggr_path}/" \
                  f"{template_schema_filename}"

            response = self.client.put(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            mp_aggr = ModelProgramLogicalFile.objects.first()
            # check metadata schema exists in the aggregation
            self.assertTrue(mp_aggr.metadata_schema_json)
            mp_aggr.metadata_schema_json = {}
            mp_aggr.save()

    def test_update_metadata_model_program(self):
        """Test that we can update all metadata for a model program aggregation."""

        mp_aggr = self._create_model_program_aggregation(expected_file_count=1)
        base_file_path = 'hs_core/tests/data/{}'
        json_file_path = base_file_path.format('model_program_meta.json')
        mp_aggr_path = mp_aggr.aggregation_name
        url = f"/hsapi/resource/{self.res.short_id}/modelprogram/meta/{mp_aggr_path}"
        with open(json_file_path) as file_obj:
            metadata_json = json.loads(file_obj.read())
        response = self.client.put(url, data=metadata_json, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mp_aggr = ModelProgramLogicalFile.objects.first()
        # check updated metadata
        self.assertEqual(mp_aggr.dataset_name, metadata_json['title'])
        self.assertEqual(mp_aggr.model_program_type, metadata_json['name'])
        self.assertEqual(mp_aggr.metadata.keywords, metadata_json['keywords'])
        self.assertEqual(mp_aggr.metadata.extra_metadata, metadata_json['additional_metadata'])
        self.assertEqual(mp_aggr.metadata.version, metadata_json['version'])
        self.assertEqual(mp_aggr.metadata.programming_languages, metadata_json['programming_languages'])
        self.assertEqual(mp_aggr.metadata.operating_systems, metadata_json['operating_systems'])
        self.assertEqual(mp_aggr.metadata.release_date.strftime("%Y-%m-%d"), metadata_json['release_date'])
        self.assertEqual(mp_aggr.metadata.website, metadata_json['website'])
        self.assertEqual(mp_aggr.metadata.code_repository, metadata_json['code_repository'])
        self.assertEqual(mp_aggr.metadata_schema_json, metadata_json['program_schema_json'])
        mp_program_file_types = []
        for mp_file_type in mp_aggr.metadata.mp_file_types.all():
            file_type = ModelProgramResourceFileType.type_name_from_type(type_number=mp_file_type.file_type)
            file_path = mp_file_type.res_file.short_path
            mp_program_file_types.append({"file_type": file_type, "file_path": file_path})
        self.assertEqual(mp_program_file_types, metadata_json['program_file_types'])

    def test_update_model_instance_meta_schema(self):
        """Test that we can update the metadata schema in a model instance using the schema from the linked
        model program aggregation"""

        mp_aggr = self._create_model_program_aggregation(expected_file_count=1, upload_folder='mp-folder')
        mi_aggr = self._create_model_instance_aggregation(expected_file_count=2)
        # link the mip aggr to mp aggregation (executed_by)
        self.assertEqual(mi_aggr.metadata.executed_by, None)
        mi_aggr.metadata.executed_by = mp_aggr
        mi_aggr.metadata.save()
        # set the metadata schema for the mp aggregation
        self.assertFalse(mp_aggr.metadata_schema_json)
        mp_aggr_path = mp_aggr.aggregation_name
        template_schema_filename = self.schema_templates[0]
        url = f"/hsapi/resource/{self.res.short_id}/modelprogram/template/meta/schema/{mp_aggr_path}/" \
              f"{template_schema_filename}"

        response = self.client.put(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertTrue(mp_aggr.metadata_schema_json)
        self.assertFalse(mi_aggr.metadata_schema_json)
        # update the meta schema for mi aggr from mp aggr
        mi_aggr_path = mi_aggr.aggregation_name
        url = f"/hsapi/resource/{self.res.short_id}/modelinstance/meta/schema/{mi_aggr_path}"
        response = self.client.put(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertTrue(mi_aggr.metadata_schema_json)

    def _create_model_program_aggregation(self, expected_file_count, upload_folder=""):
        base_file_path = 'hs_core/tests/data/{}'
        file_path = base_file_path.format('test.txt')
        if upload_folder:
            # upload_folder = 'mp-folder'
            ResourceFile.create_folder(self.res, upload_folder)
        file_to_upload = UploadedFile(file=open(file_path, 'rb'), name=os.path.basename(file_path))
        res_file = add_file_to_resource(self.res, file_to_upload, folder=upload_folder, check_target_folder=True)
        self.assertEqual(self.res.files.count(), expected_file_count)
        # create model program aggregation
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 0)
        if upload_folder:
            # set the folder to model program aggregation type
            ModelProgramLogicalFile.set_file_type(self.res, self.user, folder_path=upload_folder)
        else:
            # set the file as the model program aggregation type
            ModelProgramLogicalFile.set_file_type(self.res, self.user, file_id=res_file.id)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        mp_aggr = ModelProgramLogicalFile.objects.first()
        return mp_aggr

    def _create_model_instance_aggregation(self, expected_file_count):
        base_file_path = 'hs_core/tests/data/{}'
        file_path = base_file_path.format('test.txt')
        upload_folder = 'mi-folder/child-folder'
        ResourceFile.create_folder(self.res, upload_folder)
        file_to_upload = UploadedFile(file=open(file_path, 'rb'), name=os.path.basename(file_path))
        add_file_to_resource(self.res, file_to_upload, folder=upload_folder, check_target_folder=True)
        self.assertEqual(self.res.files.count(), expected_file_count)
        # create model instance aggregation
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 0)
        # set the folder to model instance aggregation type
        ModelInstanceLogicalFile.set_file_type(self.res, self.user, folder_path=upload_folder)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        return mi_aggr
