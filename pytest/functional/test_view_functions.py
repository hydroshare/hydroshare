import json
import os

import pytest
from django.core.files.uploadedfile import UploadedFile
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from rest_framework import status

from hs_core.hydroshare import add_file_to_resource, ResourceFile
from hs_file_types.models import ModelProgramLogicalFile, ModelInstanceLogicalFile
from hs_file_types.views import set_file_type, update_model_program_metadata, update_model_instance_metadata, \
    update_model_instance_metadata_json


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('aggr_type', ['ModelProgram', 'ModelInstance'])
def test_create_model_aggregation_from_file(composite_resource, aggr_type, mock_irods):
    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    upload_folder = None
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))
    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )
    assert res.files.count() == 1
    if aggr_type == 'ModelProgram':
        aggr_class = ModelProgramLogicalFile
    else:
        aggr_class = ModelInstanceLogicalFile
    # create model program/model instance aggregation
    assert aggr_class.objects.count() == 0
    hs_file_type = aggr_type
    url_params = {'resource_id': res.short_id,
                  'file_id': res_file.id,
                  'hs_file_type': hs_file_type
                  }
    url = reverse('set_file_type', kwargs=url_params)
    factory = RequestFactory()
    request = factory.post(url)
    request.user = user
    # this is the view function we are testing
    response = set_file_type(request, resource_id=res.short_id,
                             file_id=res_file.id, hs_file_type=hs_file_type)
    assert response.status_code == status.HTTP_201_CREATED
    assert aggr_class.objects.count() == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('aggr_type', ['ModelProgram', 'ModelInstance'])
def test_create_model_aggregation_from_folder(composite_resource, aggr_type, mock_irods):
    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    # create a folder and put a file in that folder
    aggr_folder = 'model_folder'
    ResourceFile.create_folder(res, aggr_folder)
    upload_folder = aggr_folder
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))
    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )
    assert res.files.count() == 1
    if aggr_type == 'ModelProgram':
        aggr_class = ModelProgramLogicalFile
    else:
        aggr_class = ModelInstanceLogicalFile
    # create model program/model instance aggregation
    assert aggr_class.objects.count() == 0
    hs_file_type = aggr_type
    url_params = {'resource_id': res.short_id,
                  'hs_file_type': hs_file_type
                  }
    post_data = {'folder_path': res_file.file_folder}
    url = reverse('set_file_type', kwargs=url_params)
    factory = RequestFactory()
    request = factory.post(url, data=post_data)
    request.user = user
    # this is the view function we are testing
    response = set_file_type(request, resource_id=res.short_id, hs_file_type=hs_file_type)
    assert response.status_code == status.HTTP_201_CREATED
    assert aggr_class.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_update_model_program_metadata(composite_resource_with_mp_aggregation, mock_irods):
    res, user = composite_resource_with_mp_aggregation
    mp_aggr = next(res.logical_files)
    mp_program_type = "SWAT Model Program"
    assert isinstance(mp_aggr, ModelProgramLogicalFile)
    assert mp_aggr.metadata.version is None
    assert mp_aggr.model_program_type != mp_program_type
    url_params = {'file_type_id': mp_aggr.id}
    url = reverse('update_modelprogram_metadata', kwargs=url_params)
    post_data = {"version": "2.1", "mp_program_type": mp_program_type}
    factory = RequestFactory()
    request = factory.post(url, data=post_data)
    request.user = user
    # this is the view function we are testing
    response = update_model_program_metadata(request, file_type_id=mp_aggr.id)
    assert response.status_code == status.HTTP_200_OK
    mp_aggr.metadata.refresh_from_db()
    assert mp_aggr.metadata.version == "2.1"
    mp_aggr.refresh_from_db()
    assert mp_aggr.model_program_type == mp_program_type


@pytest.mark.django_db(transaction=True)
def test_update_model_instance_metadata(composite_resource_with_mi_aggregation, mock_irods):
    res, user = composite_resource_with_mi_aggregation
    mi_aggr = next(res.logical_files)
    assert isinstance(mi_aggr, ModelInstanceLogicalFile)
    assert mi_aggr.metadata.has_model_output is False

    url_params = {'file_type_id': mi_aggr.id}
    url = reverse('update_modelinstance_metadata', kwargs=url_params)
    post_data = {"has_model_output": True}
    factory = RequestFactory()
    request = factory.post(url, data=post_data)
    request.user = user
    # this is the view function we are testing
    response = update_model_instance_metadata(request, file_type_id=mi_aggr.id)
    assert response.status_code == status.HTTP_200_OK
    mi_aggr.metadata.refresh_from_db()
    assert mi_aggr.metadata.has_model_output is True


@pytest.mark.django_db(transaction=True)
def test_update_model_instance_metadata_json(composite_resource_with_mi_mp_aggregation, mock_irods):
    res, user = composite_resource_with_mi_mp_aggregation
    logical_files = res.logical_files
    aggr1 = next(logical_files)
    if isinstance(aggr1, ModelInstanceLogicalFile):
        mi_aggr = aggr1
    else:
        mp_aggr = aggr1

    aggr2 = next(logical_files)
    if isinstance(aggr2, ModelInstanceLogicalFile):
        mi_aggr = aggr2
    else:
        mp_aggr = aggr2

    # set metadata schema for model program aggregation
    schema_file_path = 'pytest/assets/mi_schema.json'
    with open(schema_file_path, 'r') as file_obj:
        json_schema = file_obj.read()
    assert len(json_schema) > 0
    assert not mp_aggr.mi_schema_json
    mp_aggr.mi_schema_json = json.loads(json_schema)
    mp_aggr.save()
    assert mp_aggr.mi_schema_json
    assert mi_aggr.metadata.executed_by is None
    # set executed by to model program aggregation
    mi_aggr.metadata.executed_by = mp_aggr
    mi_aggr.metadata.save()
    assert not mi_aggr.metadata.metadata_json
    metadata_json_file_path = 'pytest/assets/mi_metadata.json'
    with open(metadata_json_file_path, 'r') as file_obj:
        metadata_json = file_obj.read()
    assert len(metadata_json) > 0

    url_params = {'file_type_id': mi_aggr.id}
    url = reverse('update_modelinstance_metadata_json', kwargs=url_params)
    post_data = {"metadata_json": metadata_json}
    factory = RequestFactory()
    request = factory.post(url, data=post_data)
    request.user = user
    # this is the view function we are testing
    response = update_model_instance_metadata_json(request, file_type_id=mi_aggr.id)
    assert response.status_code == status.HTTP_200_OK
    mi_aggr.metadata.refresh_from_db()
    assert len(mi_aggr.metadata.metadata_json) > 0
