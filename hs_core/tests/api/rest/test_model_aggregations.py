import glob
import json
import os

from dateutil import parser
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from hs_core import hydroshare
from hs_core.hydroshare import add_file_to_resource
from hs_core.models import ResourceFile
from hs_core.tests.api.rest.base import HSRESTTestCase
from hs_file_types.models import ModelInstanceLogicalFile, ModelProgramLogicalFile, ModelProgramResourceFileType


class TestModelAggregation(HSRESTTestCase):

    def setUp(self):
        super(TestModelAggregation, self).setUp()
        self.res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Testing Model Aggregation Related Endpoints',
            keywords=['kw1', 'kw2']
        )

        self.schema_templates = []
        template_path = settings.MODEL_PROGRAM_META_SCHEMA_TEMPLATE_PATH
        template_path = os.path.join(template_path, "*.json")
        for schema_template in glob.glob(template_path):
            template_file_name = os.path.basename(schema_template)
            self.schema_templates.append(template_file_name)

        self.unauthorized_client = APIClient()

    def tearDown(self):
        super(TestModelAggregation, self).tearDown()
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

    def test_assign_template_meta_schema_to_model_program(self):
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

    def test_update_metadata_model_program_unauthorized(self):
        """Test that an unauthorized user can't update metadata for a model program aggregation."""

        self.assertEqual(self.res.raccess.public, False)
        mp_aggr = self._create_model_program_aggregation(expected_file_count=1)
        base_file_path = 'hs_core/tests/data/{}'
        json_file_path = base_file_path.format('model_program_meta.json')
        mp_aggr_path = mp_aggr.aggregation_name
        url = f"/hsapi/resource/{self.res.short_id}/modelprogram/meta/{mp_aggr_path}"
        with open(json_file_path) as file_obj:
            metadata_json = json.loads(file_obj.read())
        # test for private resource - not allowed
        response = self.unauthorized_client.put(url, data=metadata_json, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # test for public resource - not allowed
        self.res.raccess.public = True
        self.res.raccess.save()
        response = self.unauthorized_client.put(url, data=metadata_json, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.res.raccess.public = False
        self.res.raccess.discoverable = True
        self.res.raccess.save()
        # test for discoverable resource - not allowed
        response = self.unauthorized_client.put(url, data=metadata_json, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_metadata_model_program(self):
        """Test that we can retrieve all metadata for a model program aggregation."""

        mp_aggr = self._create_model_program_aggregation(expected_file_count=1)
        # ingest some metadata to the model program aggregation
        base_file_path = 'hs_core/tests/data/{}'
        json_file_path = base_file_path.format('model_program_meta.json')
        mp_aggr_path = mp_aggr.aggregation_name
        url = f"/hsapi/resource/{self.res.short_id}/modelprogram/meta/{mp_aggr_path}"
        with open(json_file_path) as file_obj:
            metadata_json = json.loads(file_obj.read())
        response = self.client.put(url, data=metadata_json, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # retrieve model program metadata - this is the endpoint we are testing
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())

        # check the retrieved metadata
        self.assertEqual(response_json['title'], metadata_json['title'])
        self.assertEqual(response_json['keywords'], metadata_json['keywords'])
        self.assertEqual(response_json['additional_metadata'], metadata_json['additional_metadata'])
        self.assertEqual(response_json['version'], metadata_json['version'])
        self.assertEqual(response_json['programming_languages'], metadata_json['programming_languages'])
        self.assertEqual(response_json['operating_systems'], metadata_json['operating_systems'])
        release_date_out = parser.parse(response_json['release_date'])
        release_date_in = parser.parse(metadata_json['release_date'])
        self.assertEqual(release_date_in, release_date_out)
        self.assertEqual(response_json['website'], metadata_json['website'])
        self.assertEqual(response_json['code_repository'], metadata_json['code_repository'])
        self.assertEqual(response_json['program_schema_json'], metadata_json['program_schema_json'])
        self.assertEqual(response_json['program_file_types'], metadata_json['program_file_types'])

    def test_get_metadata_model_program_unauthorized(self):
        """Test that an unauthorized user can retrieve all metadata for a model program aggregation
        when the resource is public or discoverable."""

        mp_aggr = self._create_model_program_aggregation(expected_file_count=1)
        # ingest some metadata to the model program aggregation
        base_file_path = 'hs_core/tests/data/{}'
        json_file_path = base_file_path.format('model_program_meta.json')
        mp_aggr_path = mp_aggr.aggregation_name
        url = f"/hsapi/resource/{self.res.short_id}/modelprogram/meta/{mp_aggr_path}"
        with open(json_file_path) as file_obj:
            metadata_json = json.loads(file_obj.read())
        response = self.client.put(url, data=metadata_json, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # retrieve model program metadata - this is the endpoint we are testing for unauthorized user
        # test for private resource - not allowed
        self.assertEqual(self.res.raccess.public, False)
        response = self.unauthorized_client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # test for public resource - should be allowed
        self.res.raccess.public = True
        self.res.raccess.save()
        response = self.unauthorized_client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # test for discoverable resource - should be allowed
        self.res.raccess.public = False
        self.res.raccess.discoverable = True
        self.res.raccess.save()
        response = self.unauthorized_client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_model_instance_meta_schema(self):
        """Test that we can update the metadata schema in a model instance using the schema from the linked
        model program aggregation."""

        mp_aggr = self._create_model_program_aggregation(expected_file_count=1, upload_folder='mp-folder')
        mi_aggr = self._create_model_instance_aggregation(expected_file_count=2)
        # link the mi aggr to mp aggregation (executed_by)
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

    def test_update_model_instance_meta_schema_unauthorized(self):
        """Test that an unauthorized user can't update the metadata schema in a model instance using the schema
        from the linked model program aggregation."""

        mp_aggr = self._create_model_program_aggregation(expected_file_count=1, upload_folder='mp-folder')
        mi_aggr = self._create_model_instance_aggregation(expected_file_count=2)
        # link the mi aggr to mp aggregation (executed_by)
        self.assertEqual(mi_aggr.metadata.executed_by, None)
        mi_aggr.metadata.executed_by = mp_aggr
        mi_aggr.metadata.save()
        # set the metadata schema for the mp aggregation
        self.assertFalse(mp_aggr.metadata_schema_json)
        mp_aggr_path = mp_aggr.aggregation_name
        template_schema_filename = self.schema_templates[0]
        url = f"/hsapi/resource/{self.res.short_id}/modelprogram/template/meta/schema/{mp_aggr_path}/" \
              f"{template_schema_filename}"

        # test for private resource - not allowed
        self.assertEqual(self.res.raccess.public, False)
        response = self.unauthorized_client.put(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # test for public resource - not allowed
        self.res.raccess.public = True
        self.res.raccess.save()
        response = self.unauthorized_client.put(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # test for discoverable resource - not allowed
        self.res.raccess.public = False
        self.res.raccess.discoverable = True
        self.res.raccess.save()
        response = self.unauthorized_client.put(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_metadata_model_instance(self):
        """Test that we can retrieve all metadata for a model instance aggregation."""

        mp_aggr = self._create_model_program_aggregation(expected_file_count=1, upload_folder='mp-folder')
        mi_aggr = self._create_model_instance_aggregation(expected_file_count=2)
        # ingest some metadata to the model instance

        # first set the schema for the mp aggregation
        self.assertFalse(mp_aggr.metadata_schema_json)
        mp_aggr_path = mp_aggr.aggregation_name
        for template_schema_filename in self.schema_templates:
            if template_schema_filename.startswith("SWAT"):
                url = f"/hsapi/resource/{self.res.short_id}/modelprogram/template/meta/schema/{mp_aggr_path}/" \
                      f"{template_schema_filename}"
                response = self.client.put(url, format='json')
                self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
                break
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertTrue(mp_aggr.metadata_schema_json)

        base_file_path = 'hs_core/tests/data/{}'
        json_file_path = base_file_path.format('model_instance_meta.json')
        mi_aggr_path = mi_aggr.aggregation_name
        url = f"/hsapi/resource/{self.res.short_id}/modelinstance/meta/{mi_aggr_path}"
        # first just update the executed_by for the model instance aggregation
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.metadata.executed_by, None)
        response = self.client.put(url, data={"executed_by": mp_aggr.aggregation_name}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertNotEqual(mi_aggr.metadata.executed_by, None)
        # now update all metadata for the model instance aggregation including the metadata based on the schema
        with open(json_file_path) as file_obj:
            metadata_json = json.loads(file_obj.read())
            metadata_json['executed_by'] = mp_aggr.aggregation_name
        response = self.client.put(url, data=metadata_json, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # retrieve metadata of the model instance aggregation - this is the endpoint we are testing
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())

        # check retrieved metadata
        self.assertEqual(response_json['title'], metadata_json['title'])
        self.assertEqual(response_json['keywords'], metadata_json['keywords'])
        self.assertEqual(response_json['additional_metadata'], metadata_json['additional_metadata'])
        self.assertEqual(response_json['has_model_output'], metadata_json['has_model_output'])
        self.assertEqual(response_json['executed_by'], metadata_json['executed_by'])
        self.assertEqual(response_json['metadata_json'], metadata_json['metadata_json'])
        self.assertNotEqual(response_json['metadata_schema'], {})
        start_date_out = parser.parse(response_json['temporal_coverage']['start'])
        end_date_out = parser.parse(response_json['temporal_coverage']['end'])
        start_date_in = parser.parse(metadata_json['temporal_coverage']['start'])
        end_date_in = parser.parse(metadata_json['temporal_coverage']['end'])
        self.assertEqual(start_date_out, start_date_in)
        self.assertEqual(end_date_out, end_date_in)
        response_json['spatial_coverage'].pop('projection')
        self.assertEqual(response_json['spatial_coverage'], metadata_json['spatial_coverage'])

    def test_get_metadata_model_instance_unauthorized(self):
        """Test that an unauthorized user can retrieve all metadata for a model instance aggregation for
        a resource that is either public or discoverable."""

        mp_aggr = self._create_model_program_aggregation(expected_file_count=1, upload_folder='mp-folder')
        mi_aggr = self._create_model_instance_aggregation(expected_file_count=2)
        # ingest some metadata to the model instance

        # first set the schema for the mp aggregation
        self.assertFalse(mp_aggr.metadata_schema_json)
        mp_aggr_path = mp_aggr.aggregation_name
        for template_schema_filename in self.schema_templates:
            if template_schema_filename.startswith("SWAT"):
                url = f"/hsapi/resource/{self.res.short_id}/modelprogram/template/meta/schema/{mp_aggr_path}/" \
                      f"{template_schema_filename}"
                response = self.client.put(url, format='json')
                self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
                break
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertTrue(mp_aggr.metadata_schema_json)

        base_file_path = 'hs_core/tests/data/{}'
        json_file_path = base_file_path.format('model_instance_meta.json')
        mi_aggr_path = mi_aggr.aggregation_name
        url = f"/hsapi/resource/{self.res.short_id}/modelinstance/meta/{mi_aggr_path}"
        # first just update the executed_by for the model instance aggregation
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.metadata.executed_by, None)
        response = self.client.put(url, data={"executed_by": mp_aggr.aggregation_name}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertNotEqual(mi_aggr.metadata.executed_by, None)
        # now update all metadata for the model instance aggregation including the metadata based on the schema
        with open(json_file_path) as file_obj:
            metadata_json = json.loads(file_obj.read())
            metadata_json['executed_by'] = mp_aggr.aggregation_name
        response = self.client.put(url, data=metadata_json, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # retrieve metadata of the model instance aggregation - this is the endpoint we are testing
        # test for private resource - should return 403
        self.assertEqual(self.res.raccess.public, False)
        response = self.unauthorized_client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # test for public resource - should return 200
        self.res.raccess.public = True
        self.res.raccess.save()
        response = self.unauthorized_client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # test for discoverable resource - should return 200
        self.res.raccess.discoverable = True
        self.res.raccess.save()
        response = self.unauthorized_client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_metadata_model_instance(self):
        """Test that we can update all metadata for a model instance aggregation."""

        mp_aggr = self._create_model_program_aggregation(expected_file_count=1, upload_folder='mp-folder')
        mi_aggr = self._create_model_instance_aggregation(expected_file_count=2)
        # first set the schema for the mp aggregation
        self.assertFalse(mp_aggr.metadata_schema_json)
        mp_aggr_path = mp_aggr.aggregation_name
        for template_schema_filename in self.schema_templates:
            if template_schema_filename.startswith("SWAT"):
                url = f"/hsapi/resource/{self.res.short_id}/modelprogram/template/meta/schema/{mp_aggr_path}/" \
                      f"{template_schema_filename}"
                response = self.client.put(url, format='json')
                self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
                break
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertTrue(mp_aggr.metadata_schema_json)

        base_file_path = 'hs_core/tests/data/{}'
        json_file_path = base_file_path.format('model_instance_meta.json')
        mi_aggr_path = mi_aggr.aggregation_name
        url = f"/hsapi/resource/{self.res.short_id}/modelinstance/meta/{mi_aggr_path}"
        # first just update the executed_by for the model instance aggregation
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.metadata.executed_by, None)
        response = self.client.put(url, data={"executed_by": mp_aggr.aggregation_name}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertNotEqual(mi_aggr.metadata.executed_by, None)
        # now update all metadata for the model instance aggregation including the metadata based on the schema
        with open(json_file_path) as file_obj:
            metadata_json = json.loads(file_obj.read())
            metadata_json['executed_by'] = mp_aggr.aggregation_name
        response = self.client.put(url, data=metadata_json, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        # check updated metadata
        self.assertEqual(mi_aggr.dataset_name, metadata_json['title'])
        self.assertEqual(mi_aggr.metadata.keywords, metadata_json['keywords'])
        self.assertEqual(mi_aggr.metadata.extra_metadata, metadata_json['additional_metadata'])
        self.assertEqual(mi_aggr.metadata.has_model_output, metadata_json['has_model_output'])
        self.assertEqual(mi_aggr.metadata.executed_by.aggregation_name, metadata_json['executed_by'])
        self.assertEqual(mi_aggr.metadata.metadata_json, metadata_json['metadata_json'])
        temporal_coverage = mi_aggr.metadata.temporal_coverage.value
        start_date = parser.parse(temporal_coverage['start'])
        end_date = parser.parse(temporal_coverage['end'])
        start_date_in = parser.parse(metadata_json['temporal_coverage']['start'])
        end_date_in = parser.parse(metadata_json['temporal_coverage']['end'])
        self.assertEqual(start_date, start_date_in)
        self.assertEqual(end_date, end_date_in)
        spatial_coverage = mi_aggr.metadata.spatial_coverage.value
        spatial_coverage.pop('projection')
        input_cove_type = metadata_json['spatial_coverage'].pop('type')
        self.assertEqual(spatial_coverage, metadata_json['spatial_coverage'])
        self.assertEqual(mi_aggr.metadata.spatial_coverage.type, input_cove_type)

    def test_update_metadata_model_instance_unauthorized(self):
        """Test that an unauthorized user can't update metadata for a model instance aggregation."""

        mp_aggr = self._create_model_program_aggregation(expected_file_count=1, upload_folder='mp-folder')
        mi_aggr = self._create_model_instance_aggregation(expected_file_count=2)
        # first set the schema for the mp aggregation
        self.assertFalse(mp_aggr.metadata_schema_json)
        mp_aggr_path = mp_aggr.aggregation_name
        for template_schema_filename in self.schema_templates:
            if template_schema_filename.startswith("SWAT"):
                url = f"/hsapi/resource/{self.res.short_id}/modelprogram/template/meta/schema/{mp_aggr_path}/" \
                      f"{template_schema_filename}"
                response = self.client.put(url, format='json')
                self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
                break
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertTrue(mp_aggr.metadata_schema_json)

        mi_aggr_path = mi_aggr.aggregation_name
        url = f"/hsapi/resource/{self.res.short_id}/modelinstance/meta/{mi_aggr_path}"
        # first just update the executed_by for the model instance aggregation
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.metadata.executed_by, None)
        # test for private resource - not allowed
        self.assertEqual(self.res.raccess.public, False)
        response = self.unauthorized_client.put(url, data={"executed_by": mp_aggr.aggregation_name}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # test for public resource - not allowed
        self.res.raccess.public = True
        self.res.raccess.save()
        response = self.unauthorized_client.put(url, data={"executed_by": mp_aggr.aggregation_name}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # test for discoverable resource - not allowed
        self.res.raccess.discoverable = True
        self.res.raccess.save()
        response = self.unauthorized_client.put(url, data={"executed_by": mp_aggr.aggregation_name}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _create_model_program_aggregation(self, expected_file_count, upload_folder=""):
        base_file_path = 'hs_core/tests/data/{}'
        file_path = base_file_path.format('test.txt')
        if upload_folder:
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
