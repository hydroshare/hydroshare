import json
import os

import pytest
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse
from django.test import RequestFactory
from rest_framework import status

from hs_core.hydroshare import add_file_to_resource, ResourceFile, add_resource_files
from hs_file_types.models import (
    ModelProgramLogicalFile,
    ModelInstanceLogicalFile,
    NetCDFLogicalFile,
    GeoRasterLogicalFile,
    TimeSeriesLogicalFile,
    GeoFeatureLogicalFile,
    CSVLogicalFile,
)
from hs_file_types.views import (
    set_file_type,
    update_model_program_metadata,
    update_model_instance_metadata,
    update_model_instance_metadata_json,
    move_aggregation,
    update_csv_table_schema_metadata,
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('aggr_type', ['ModelProgram', 'ModelInstance'])
def test_create_model_aggregation_from_file(composite_resource, aggr_type, mock_irods):
    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    upload_folder = ''
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
    assert not res.dangling_aggregations_exist()


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
    assert not res.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_update_csv_aggregation_table_schema(composite_resource, mock_irods):
    res, user = composite_resource
    file_path = 'pytest/assets/csv_with_header_and_data.csv'
    upload_folder = ''
    assert CSVLogicalFile.objects.count() == 0
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))
    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )
    assert res.files.count() == 1
    assert CSVLogicalFile.objects.count() == 0

    # create a CSV aggregation
    CSVLogicalFile.set_file_type(res, user, res_file.id)
    # there should be a CSV aggregation now
    assert CSVLogicalFile.objects.count() == 1
    csv_aggr = CSVLogicalFile.objects.first()
    csv_metadata = csv_aggr.metadata
    table_schema_model = csv_metadata.get_table_schema_model()
    url_params = {'file_type_id': csv_aggr.id}
    url = reverse('update_csv_table_schema', kwargs=url_params)
    post_data = {}
    for col_no, col in enumerate(table_schema_model.table.columns):
        col_title_key = f"column-{col_no}-titles"
        post_data[col_title_key] = col.titles
        col_data_type_key = f"column-{col_no}-datatype"
        post_data[col_data_type_key] = col.datatype
        col_desc_key = f"column-{col_no}-description"
        post_data[col_desc_key] = f"description for column {col_no}"

    factory = RequestFactory()
    request = factory.post(url, data=post_data)
    request.user = user
    # this is the view function we are testing
    response = update_csv_table_schema_metadata(request, file_type_id=csv_aggr.id)
    assert response.status_code == status.HTTP_200_OK
    csv_aggr.metadata.refresh_from_db()
    csv_metadata = csv_aggr.metadata
    table_schema_model = csv_metadata.get_table_schema_model()
    # check that the table schema was updated
    for col_no, col in enumerate(table_schema_model.table.columns):
        assert col.titles == post_data[f"column-{col_no}-titles"]
        assert col.datatype == post_data[f"column-{col_no}-datatype"]
        assert col.description == f"description for column {col_no}"

    csv_aggr.refresh_from_db()
    assert csv_aggr.metadata.is_dirty
    assert not res.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_update_model_program_metadata(composite_resource_with_mp_aggregation, mock_irods):
    res, user = composite_resource_with_mp_aggregation
    mp_aggr = next(res.logical_files)
    code_repo = "https://github.com/swat"
    version = "2.1"
    assert isinstance(mp_aggr, ModelProgramLogicalFile)
    assert mp_aggr.metadata.version is None

    url_params = {'file_type_id': mp_aggr.id}
    url = reverse('update_modelprogram_metadata', kwargs=url_params)
    post_data = {"version": version, "code_repository": code_repo}
    factory = RequestFactory()
    request = factory.post(url, data=post_data)
    request.user = user
    # this is the view function we are testing
    response = update_model_program_metadata(request, file_type_id=mp_aggr.id)
    assert response.status_code == status.HTTP_200_OK
    mp_aggr.metadata.refresh_from_db()
    assert mp_aggr.metadata.version == version
    assert mp_aggr.metadata.code_repository == code_repo
    mp_aggr.refresh_from_db()

    assert mp_aggr.metadata.is_dirty
    assert not res.dangling_aggregations_exist()


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
    assert mi_aggr.metadata.is_dirty
    assert not res.dangling_aggregations_exist()


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
    assert not mp_aggr.metadata_schema_json
    mp_aggr.metadata_schema_json = json.loads(json_schema)
    mp_aggr.save()
    assert mp_aggr.metadata_schema_json
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
    assert mi_aggr.metadata.is_dirty
    assert not res.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('move_aggr_cls', [NetCDFLogicalFile, GeoRasterLogicalFile, TimeSeriesLogicalFile,
                                           GeoFeatureLogicalFile, CSVLogicalFile])
def test_move_aggr_into_model_instance_aggr(composite_resource_with_mi_aggregation_folder, move_aggr_cls, mock_irods):
    """test that we can move any of the following aggregations into a folder that represents a
    model instance aggregation
    1- Netcdf aggr
    2- GeoFeature aggr
    3- Raster aggr
    4- Timeseries aggr
    5- CSV aggr
    """

    res, user = composite_resource_with_mi_aggregation_folder
    mi_aggr = next(res.logical_files)
    assert isinstance(mi_aggr, ModelInstanceLogicalFile)
    mi_folder = mi_aggr.folder

    # create aggr (to be moved) at the root
    assert move_aggr_cls.objects.count() == 0
    if move_aggr_cls == NetCDFLogicalFile:
        file_name = "netcdf_valid.nc"
        expected_aggr_name = file_name
        aggr_class_name = "NetCDFLogicalFile"
    elif move_aggr_cls == GeoRasterLogicalFile:
        file_name = 'small_logan.tif'
        expected_aggr_name = 'small_logan.vrt'
        aggr_class_name = "GeoRasterLogicalFile"
    elif move_aggr_cls == TimeSeriesLogicalFile:
        file_name = 'ODM2_Multi_Site_One_Variable.sqlite'
        expected_aggr_name = file_name
        aggr_class_name = "TimeSeriesLogicalFile"
    elif move_aggr_cls == GeoFeatureLogicalFile:
        file_name = 'states.shp'
        expected_aggr_name = file_name
        aggr_class_name = "GeoFeatureLogicalFile"
    else:
        file_name = 'csv_with_header_and_data.csv'
        expected_aggr_name = file_name
        aggr_class_name = "CSVLogicalFile"

    if move_aggr_cls in (TimeSeriesLogicalFile, GeoFeatureLogicalFile, CSVLogicalFile):
        files_to_upload = []
        if move_aggr_cls == GeoFeatureLogicalFile:
            for shp_file in (file_name, 'states.shx', 'states.dbf', 'states.prj'):
                upload_file_path = 'hs_file_types/tests/data/{}'.format(shp_file)
                file_to_upload = UploadedFile(file=open(upload_file_path, 'rb'),
                                              name=os.path.basename(upload_file_path))
                files_to_upload.append(file_to_upload)
        else:
            upload_file_path = 'hs_file_types/tests/data/{}'.format(file_name)
            files_to_upload.append(UploadedFile(file=open(upload_file_path, 'rb'),
                                                name=os.path.basename(upload_file_path)))

    else:
        upload_file_path = 'hs_file_types/tests/{}'.format(file_name)
        files_to_upload = [UploadedFile(file=open(upload_file_path, 'rb'), name=os.path.basename(upload_file_path))]

    # aggregation is created as part of auto aggregation creation
    add_resource_files(res.short_id, *files_to_upload, folder="")

    assert move_aggr_cls.objects.count() == 1
    move_aggr = move_aggr_cls.objects.first()
    assert move_aggr.aggregation_name == expected_aggr_name

    # move the aggr (auto created) into the folder (mi_folder) that represents model instance aggr
    # using the 'move_aggregation' view function to do the aggregation move
    url_params = {'resource_id': res.short_id,
                  'file_type_id': move_aggr.id,
                  "hs_file_type": aggr_class_name,
                  "tgt_path": mi_folder
                  }
    url = reverse('move_aggregation', kwargs=url_params)
    factory = RequestFactory()
    request = factory.post(url)
    request.user = user
    response = move_aggregation(request, resource_id=res.short_id, hs_file_type=aggr_class_name,
                                file_type_id=move_aggr.id, tgt_path=mi_folder, run_async=False)
    assert response.status_code == status.HTTP_200_OK
    assert move_aggr_cls.objects.count() == 1
    move_aggr.refresh_from_db()
    assert move_aggr.aggregation_name == "{}/{}".format(mi_folder, expected_aggr_name)
    assert move_aggr.metadata.is_dirty
    assert mi_aggr.metadata.is_dirty
    assert not res.dangling_aggregations_exist()
