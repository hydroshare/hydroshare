import os

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from hs_core.hydroshare import add_file_to_resource, ResourceFile, add_resource_files
from hs_core.views.utils import move_or_rename_file_or_folder
from hs_file_types.forms import ModelInstanceMetadataValidationForm
from hs_file_types.models import (
    ModelInstanceLogicalFile,
    ModelProgramLogicalFile,
    NetCDFLogicalFile,
    GeoRasterLogicalFile,
    GeoFeatureLogicalFile,
    GenericLogicalFile,
    TimeSeriesLogicalFile,
    RefTimeseriesLogicalFile,
    FileSetLogicalFile,
    CSVLogicalFile,
)


@pytest.mark.django_db(transaction=True)
def test_link_model_aggregations_same_resource(composite_resource_with_mi_aggregation, mock_irods):
    """Test that we can link one model instance aggregation to one model program aggregation within the same resource"""

    res, user = composite_resource_with_mi_aggregation
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is not related to any model program aggregation
    assert mi_aggr.metadata.executed_by is None
    # create a model program aggregation
    file_path = 'pytest/assets/logan.vrt'
    upload_folder = ''
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

    assert ModelProgramLogicalFile.objects.count() == 0
    # set file to model program aggregation type
    ModelProgramLogicalFile.set_file_type(res, user, res_file.id)
    assert ModelProgramLogicalFile.objects.count() == 1
    mp_aggr = ModelProgramLogicalFile.objects.first()
    # link model instance aggregation to model program aggregation
    mi_validation_form = ModelInstanceMetadataValidationForm(data={"executed_by": mp_aggr.id}, user=user, resource=res)
    assert mi_validation_form.is_valid()
    mi_validation_form.update_metadata(metadata=mi_aggr.metadata)
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is related to model program aggregation
    assert mi_aggr.metadata.executed_by is not None
    assert not res.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_model_instance_on_model_program_delete(composite_resource_with_mi_aggregation, mock_irods):
    """Test that when we remove/delete a model program aggregation that the linked model instance aggregation does not
    get deleted and the metadata of the model instance aggregation is set to dirty"""

    res, user = composite_resource_with_mi_aggregation
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is not related to any model program aggregation
    assert mi_aggr.metadata.executed_by is None
    # create a model program aggregation
    file_path = 'pytest/assets/logan.vrt'
    upload_folder = ''
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

    assert ModelProgramLogicalFile.objects.count() == 0
    # set file to model program aggregation type
    ModelProgramLogicalFile.set_file_type(res, user, res_file.id)
    assert ModelProgramLogicalFile.objects.count() == 1
    mp_aggr = ModelProgramLogicalFile.objects.first()
    # link model instance aggregation to model program aggregation
    mi_validation_form = ModelInstanceMetadataValidationForm(data={"executed_by": mp_aggr.id}, user=user, resource=res)
    assert mi_validation_form.is_valid()
    mi_validation_form.update_metadata(metadata=mi_aggr.metadata)
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is related to model program aggregation
    assert mi_aggr.metadata.executed_by is not None
    assert mi_aggr.metadata.is_dirty is True
    # remove/delete mp_aggregation
    mp_aggr.remove_aggregation()
    assert ModelProgramLogicalFile.objects.count() == 0
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is not related to any model program aggregation
    assert mi_aggr.metadata.executed_by is None
    # check that mi_aggr metadata is set to dirty
    assert mi_aggr.metadata.is_dirty is True
    assert not res.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_model_instance_on_model_program_rename_1(composite_resource_with_mi_aggregation, mock_irods):
    """Test that when we rename a file that represents a model program aggregation then the linked model instance
    aggregation metadata is set to dirty"""

    res, user = composite_resource_with_mi_aggregation
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is not related to any model program aggregation
    assert mi_aggr.metadata.executed_by is None
    # create a model program aggregation
    file_path = 'pytest/assets/logan.vrt'
    upload_folder = ''
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

    assert ModelProgramLogicalFile.objects.count() == 0
    # set file to model program aggregation type
    ModelProgramLogicalFile.set_file_type(res, user, res_file.id)
    assert ModelProgramLogicalFile.objects.count() == 1
    mp_aggr = ModelProgramLogicalFile.objects.first()
    # link model instance aggregation to model program aggregation
    mi_validation_form = ModelInstanceMetadataValidationForm(data={"executed_by": mp_aggr.id}, user=user, resource=res)
    assert mi_validation_form.is_valid()
    mi_validation_form.update_metadata(metadata=mi_aggr.metadata)
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is related to model program aggregation
    assert mi_aggr.metadata.executed_by is not None
    assert mi_aggr.metadata.is_dirty is True
    # rename the model program file name
    src_path = 'data/contents/{}'.format(res_file.file_name)
    tgt_path = 'data/contents/{}'.format("logan_1.vrt")
    move_or_rename_file_or_folder(user, res.short_id, src_path, tgt_path)
    assert ModelProgramLogicalFile.objects.count() == 1
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr metadata is set to dirty
    assert mi_aggr.metadata.is_dirty is True
    assert not res.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_model_instance_on_model_program_rename_2(composite_resource_with_mi_aggregation, mock_irods):
    """Test that when we rename a folder that represents a model program aggregation then the linked model instance
    aggregation metadata is set to dirty"""

    res, user = composite_resource_with_mi_aggregation
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is not related to any model program aggregation
    assert mi_aggr.metadata.executed_by is None
    # create a model program aggregation
    file_path = 'pytest/assets/logan.vrt'
    mp_folder = "mp_folder"
    ResourceFile.create_folder(res, mp_folder)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    add_file_to_resource(
        res, file_to_upload, folder=mp_folder, check_target_folder=True
    )

    assert ModelProgramLogicalFile.objects.count() == 0
    # set file to model program aggregation type
    ModelProgramLogicalFile.set_file_type(res, user, folder_path=mp_folder)
    assert ModelProgramLogicalFile.objects.count() == 1
    mp_aggr = ModelProgramLogicalFile.objects.first()
    # link model instance aggregation to model program aggregation
    mi_validation_form = ModelInstanceMetadataValidationForm(data={"executed_by": mp_aggr.id}, user=user, resource=res)
    assert mi_validation_form.is_valid()
    mi_validation_form.update_metadata(metadata=mi_aggr.metadata)
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is related to model program aggregation
    assert mi_aggr.metadata.executed_by is not None
    assert mi_aggr.metadata.is_dirty is True
    # rename the model program file name
    src_path = 'data/contents/{}'.format(mp_folder)
    tgt_path = 'data/contents/{}'.format("{}_1".format(mp_folder))
    move_or_rename_file_or_folder(user, res.short_id, src_path, tgt_path)
    assert ModelProgramLogicalFile.objects.count() == 1
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr metadata is set to dirty
    assert mi_aggr.metadata.is_dirty is True
    assert not res.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_set_metadata(composite_resource_with_mi_aggregation, mock_irods):
    """Test that we can store all metadata items for a model instance aggregation"""

    res, _ = composite_resource_with_mi_aggregation
    mi_aggr = ModelInstanceLogicalFile.objects.first()

    # test extra metadata
    assert not mi_aggr.metadata.extra_metadata
    extra_meta = {'key1': 'value 1', 'key2': 'value 2'}
    mi_aggr.metadata.extra_metadata = extra_meta
    mi_aggr.metadata.save()
    assert mi_aggr.metadata.extra_metadata == extra_meta

    # test keywords
    assert not mi_aggr.metadata.keywords
    keywords = ['kw-1', 'kw-2']
    mi_aggr.metadata.keywords = keywords
    mi_aggr.metadata.save()
    assert mi_aggr.metadata.keywords == keywords

    # test coverage metadata
    assert not mi_aggr.metadata.coverages.all()
    value_dict = {'name': 'Name for period coverage', 'start': '1/1/2000', 'end': '12/12/2012'}
    temp_cov = mi_aggr.metadata.create_element('coverage', type='period', value=value_dict)
    assert temp_cov.value['name'] == 'Name for period coverage'
    assert temp_cov.value['start'] == '1/1/2000'
    assert temp_cov.value['end'] == '12/12/2012'
    assert mi_aggr.metadata.coverages.all().count() == 1

    value_dict = {'east': '56.45678', 'north': '12.6789', 'units': 'Decimal degree'}
    spatial_cov = mi_aggr.metadata.create_element('coverage', type='point', value=value_dict)
    assert spatial_cov.value['projection'] == 'WGS 84 EPSG:4326'
    assert spatial_cov.value['units'] == 'Decimal degree'
    assert spatial_cov.value['north'] == 12.6789
    assert spatial_cov.value['east'] == 56.45678
    assert mi_aggr.metadata.coverages.all().count() == 2
    # test model output metadata
    assert not mi_aggr.metadata.has_model_output
    mi_aggr.metadata.has_model_output = True
    mi_aggr.metadata.save()
    # test setting metadata json
    assert not mi_aggr.metadata.metadata_json
    # set mi metadata json from the content of the following file
    schema_file_path = 'pytest/assets/mi_metadata.json'
    with open(schema_file_path, 'r') as file_obj:
        meta_json = file_obj.read()
    assert len(meta_json) > 0
    mi_aggr.metadata.metadata_json = meta_json
    mi_aggr.metadata.save()
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert mi_aggr.metadata.metadata_json
    assert not res.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_auto_netcdf_aggregation_creation(composite_resource_with_mi_aggregation_folder, mock_irods):
    """Test that when a netcdf file is uploaded to a folder that represents a model instance aggregation,
    a netcdf aggregation is created automatically"""

    resource, _ = composite_resource_with_mi_aggregation_folder
    mi_aggr_path = ModelInstanceLogicalFile.objects.first().aggregation_name

    assert NetCDFLogicalFile.objects.count() == 0
    # upload a netcdf file to the mi_aggr_path - folder that represents the model instance aggregation
    nc_file_name = "netcdf_valid.nc"
    netcdf_file_path = "hs_file_types/tests/{}".format(nc_file_name)
    _add_files_to_resource(resource=resource, files_to_add=[netcdf_file_path], upload_folder=mi_aggr_path)
    # there should be three resource file - one generated by netcdf aggregation
    assert resource.files.all().count() == 3
    assert NetCDFLogicalFile.objects.count() == 1
    # the netcdf file added to the model instance folder should be part of a new netcdf aggregation
    nc_res_file = ResourceFile.get(resource=resource,
                                   file=nc_file_name, folder=mi_aggr_path)
    assert nc_res_file.has_logical_file
    # the netcdf aggregation should contain 2 files - nc and the txt files
    assert NetCDFLogicalFile.objects.first().files.count() == 2
    assert not resource.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_auto_raster_aggregation_creation(composite_resource_with_mi_aggregation_folder, mock_irods):
    """Test that when a raster file (.tif) is uploaded to a folder that represents a model instance aggregation,
    a raster aggregation is created automatically"""

    resource, _ = composite_resource_with_mi_aggregation_folder
    mi_aggr_path = ModelInstanceLogicalFile.objects.first().aggregation_name
    assert GeoRasterLogicalFile.objects.count() == 0
    # upload a raster file to the mi_aggr_path - folder that represents the model instance aggregation
    raster_file_name = 'small_logan.tif'
    raster_file_path = 'hs_file_types/tests/{}'.format(raster_file_name)
    _add_files_to_resource(resource=resource, files_to_add=[raster_file_path], upload_folder=mi_aggr_path)

    # there should be three resource files ( one extra vrt file added as part of raster aggregation creation)
    assert resource.files.all().count() == 3

    # there should be one raster aggregation now
    assert GeoRasterLogicalFile.objects.count() == 1

    # the tif file added to the model instance folder should be part of a new raster aggregation
    raster_res_file = ResourceFile.get(resource=resource,
                                       file=raster_file_name, folder=mi_aggr_path)
    assert raster_res_file.has_logical_file

    # the raster aggregation should contain 2 files (tif and vrt)
    assert GeoRasterLogicalFile.objects.first().files.count() == 2
    assert not resource.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_auto_geofeature_aggregation_creation(composite_resource_with_mi_aggregation_folder, mock_irods):
    """Test that when files that represents a geofeature are uploaded to a folder that
    represents a model instance, a geofeature aggregation is created automatically"""

    resource, _ = composite_resource_with_mi_aggregation_folder
    mi_aggr_path = ModelInstanceLogicalFile.objects.first().aggregation_name

    assert GeoFeatureLogicalFile.objects.count() == 0
    # upload all 4 geo feature files the mi_aggr_ptah - folder that represents the model instance aggregation
    base_data_file_path = 'hs_file_types/tests/data/{}'
    shp_file_name = "states.shp"
    shp_file_path = base_data_file_path.format(shp_file_name)
    shx_file_name = "states.shx"
    shx_file_path = base_data_file_path.format(shx_file_name)
    dbf_file_name = "states.dbf"
    dbf_file_path = base_data_file_path.format(dbf_file_name)
    prj_file_name = "states.prj"
    prj_file_path = base_data_file_path.format(prj_file_name)
    geo_feature_files = [shp_file_path, shx_file_path, dbf_file_path, prj_file_path]
    _add_files_to_resource(resource=resource, files_to_add=geo_feature_files, upload_folder=mi_aggr_path)
    # there should be five resource files
    assert resource.files.all().count() == 5
    # the shp file added to the model instance folder should be part of a new geo feature aggregation
    shp_res_file = ResourceFile.get(resource=resource, file=shp_file_name, folder=mi_aggr_path)
    assert shp_res_file.has_logical_file

    # the geo feature aggregation should contain 4 files that we uploaded
    assert GeoFeatureLogicalFile.objects.first().files.count() == 4
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert mi_aggr.metadata.is_dirty
    assert not resource.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_auto_timeseries_aggregation_creation(composite_resource_with_mi_aggregation_folder, mock_irods):
    """Test that when a timeseries sqlite file is uploaded to a folder that
    represents a model instance, a timeseries aggregation is created automatically from that sqlite file"""

    resource, _ = composite_resource_with_mi_aggregation_folder
    mi_aggr_path = ModelInstanceLogicalFile.objects.first().aggregation_name
    assert TimeSeriesLogicalFile.objects.count() == 0
    # upload a sqlite file to the mi_aggr_path - folder that represents the model instance aggregation
    sqlite_file_name = 'ODM2_Multi_Site_One_Variable.sqlite'
    sqlite_file_path = 'hs_file_types/tests/data/{}'.format(sqlite_file_name)
    _add_files_to_resource(resource=resource, files_to_add=[sqlite_file_path], upload_folder=mi_aggr_path)

    # there should be 2 resource files
    assert resource.files.all().count() == 2
    # the sqlite file added to the model instance folder should be part of a new timeseries aggregation
    sqlite_res_file = ResourceFile.get(resource=resource,
                                       file=sqlite_file_name, folder=mi_aggr_path)
    assert sqlite_res_file.has_logical_file
    assert TimeSeriesLogicalFile.objects.count() == 1
    assert ModelInstanceLogicalFile.objects.first().files.count() == 1
    # the timeseries aggregation should contain 1 file
    assert TimeSeriesLogicalFile.objects.first().files.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert mi_aggr.metadata.is_dirty
    assert not resource.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_auto_csv_aggregation_creation(composite_resource_with_mi_aggregation_folder, mock_irods):
    """Test that when a csv file is uploaded to a folder that represents a model instance aggregation,
    a csv aggregation is created automatically"""

    resource, _ = composite_resource_with_mi_aggregation_folder
    mi_aggr_path = ModelInstanceLogicalFile.objects.first().aggregation_name
    assert CSVLogicalFile.objects.count() == 0
    # upload a csv file to the mi_aggr_path - folder that represents the model instance aggregation
    csv_file_name = 'csv_with_header_and_data.csv'
    csv_file_path = 'hs_file_types/tests/data/{}'.format(csv_file_name)
    _add_files_to_resource(resource=resource, files_to_add=[csv_file_path], upload_folder=mi_aggr_path)

    # there should be 2 resource files
    assert resource.files.all().count() == 2
    # the csv file added to the model instance folder should be part of a new csv aggregation
    csv_res_file = ResourceFile.get(resource=resource,
                                    file=csv_file_name, folder=mi_aggr_path)
    assert csv_res_file.has_logical_file
    # the csv aggregation should contain 1 file
    assert CSVLogicalFile.objects.count() == 1
    assert CSVLogicalFile.objects.first().files.count() == 1

    assert ModelInstanceLogicalFile.objects.first().files.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert mi_aggr.metadata.is_dirty
    assert not resource.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_auto_ref_timeseries_aggregation_creation(composite_resource_with_mi_aggregation_folder, mock_irods):
    """Test that when a ref timeseries json file is uploaded to a folder that
    represents a model instance aggregation, a ref timeseries aggregation is created automatically
    from that json file"""

    resource, _ = composite_resource_with_mi_aggregation_folder
    assert ModelInstanceLogicalFile.objects.first().files.count() == 1
    mi_aggr_path = ModelInstanceLogicalFile.objects.first().aggregation_name
    assert RefTimeseriesLogicalFile.objects.count() == 0
    # upload a ref timeseries json file to the mi_aggr_path - folder that represents the model instance aggregation
    ref_timeseries_file_name = 'multi_sites_formatted_version1.0.refts.json'
    ref_timeseries_file_path = 'hs_file_types/tests/{}'.format(ref_timeseries_file_name)
    _add_files_to_resource(resource=resource, files_to_add=[ref_timeseries_file_path], upload_folder=mi_aggr_path)

    # there should be 2 resource files
    assert resource.files.all().count() == 2
    # the json file added to the model instance folder should be part of a new ref timeseries aggregation
    ref_ts_res_file = ResourceFile.get(resource=resource,
                                       file=ref_timeseries_file_name, folder=mi_aggr_path)
    assert ref_ts_res_file.has_logical_file
    assert RefTimeseriesLogicalFile.objects.count() == 1
    assert ModelInstanceLogicalFile.objects.first().files.count() == 1
    # ref timeseries aggregation should contain 1 file
    assert RefTimeseriesLogicalFile.objects.first().files.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert mi_aggr.metadata.is_dirty
    assert not resource.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_canot_create_fileset_within_mi_aggregation(composite_resource_with_mi_aggregation_folder, mock_irods):
    """Test that one can't create a fileset aggregation inside a folder that represents a model instance aggregation"""

    resource, user = composite_resource_with_mi_aggregation_folder
    mi_aggr_path = ModelInstanceLogicalFile.objects.first().aggregation_name
    file_path = 'pytest/assets/logan.vrt'
    fs_folder = 'fileset_folder'
    fs_folder_path = os.path.join(mi_aggr_path, fs_folder)
    ResourceFile.create_folder(resource, fs_folder)
    _add_files_to_resource(resource=resource, files_to_add=[file_path], upload_folder=fs_folder_path)
    # trying to set folder to fileset logical file type (aggregation) should fail
    assert FileSetLogicalFile.objects.count() == 0
    with pytest.raises(ValidationError):
        FileSetLogicalFile.set_file_type(resource, user, folder_path=fs_folder_path)

    assert FileSetLogicalFile.objects.count() == 0
    assert not resource.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_canot_create_mi_aggregation_within_mi_aggregation(composite_resource_with_mi_aggregation_folder, mock_irods):
    """Test that one can't create a model instance aggregation inside a folder that represents a model
    instance aggregation"""

    resource, user = composite_resource_with_mi_aggregation_folder
    mi_aggr_path = ModelInstanceLogicalFile.objects.first().aggregation_name
    assert ModelInstanceLogicalFile.objects.count() == 1
    file_path = 'pytest/assets/logan.vrt'
    mi_sub_folder = 'mi_sub_folder'
    mi_sub_folder_path = os.path.join(mi_aggr_path, mi_sub_folder)
    ResourceFile.create_folder(resource, mi_sub_folder)
    _add_files_to_resource(resource=resource, files_to_add=[file_path], upload_folder=mi_sub_folder_path)
    # trying to set folder to model instance should fail
    assert ModelInstanceLogicalFile.objects.count() == 1
    with pytest.raises(ValidationError):
        ModelInstanceLogicalFile.set_file_type(resource, user, folder_path=mi_sub_folder_path)

    assert ModelInstanceLogicalFile.objects.count() == 1
    assert not resource.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_move_single_file_aggr_into_model_instance_aggregation(composite_resource, mock_irods):
    """ test that we can move a single file aggregation into a folder that represents a
    model instance aggregation"""

    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    mi_folder = 'mi_folder'
    ResourceFile.create_folder(res, mi_folder)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    add_file_to_resource(res, file_to_upload, folder=mi_folder, check_target_folder=True)
    assert res.files.count() == 1
    # at this point there should not be any model instance aggregation
    assert ModelInstanceLogicalFile.objects.count() == 0
    # set folder to model instance aggregation type
    ModelInstanceLogicalFile.set_file_type(resource=res, user=user, folder_path=mi_folder)
    res_file = res.files.first()
    assert res_file.has_logical_file
    # file has folder
    assert res_file.file_folder == mi_folder
    assert ModelInstanceLogicalFile.objects.count() == 1
    # create a single file aggregation
    single_file_name = 'logan.vrt'
    file_path = 'pytest/assets/{}'.format(single_file_name)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    res_file = add_file_to_resource(res, file_to_upload, check_target_folder=True)
    # set file to generic logical file type (aggregation)
    GenericLogicalFile.set_file_type(res, user, res_file.id)
    assert GenericLogicalFile.objects.count() == 1
    # moving the logan.vrt file into mi_folder should be successful
    src_path = 'data/contents/{}'.format(single_file_name)
    tgt_path = 'data/contents/{}/{}'.format(mi_folder, single_file_name)

    move_or_rename_file_or_folder(user, res.short_id, src_path, tgt_path)
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert mi_aggr.metadata.is_dirty
    assert not res.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_move_single_file_into_model_instance_aggregation(composite_resource, mock_irods):
    """ test that we move a single file into a folder that represents a
    model instance aggregation the moved file becomes part of the model instance aggregation"""

    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    mi_folder = 'mi_folder'
    ResourceFile.create_folder(res, mi_folder)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    add_file_to_resource(res, file_to_upload, folder=mi_folder, check_target_folder=True)
    assert res.files.count() == 1
    # at this point there should not be any model instance aggregation
    assert ModelInstanceLogicalFile.objects.count() == 0
    # set folder to model instance aggregation type
    ModelInstanceLogicalFile.set_file_type(resource=res, user=user, folder_path=mi_folder)
    res_file = res.files.first()
    assert res_file.has_logical_file
    # file has folder
    assert res_file.file_folder == mi_folder
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert mi_aggr.files.count() == 1
    # upload another file to the resource
    single_file_name = 'logan.vrt'
    file_path = 'pytest/assets/{}'.format(single_file_name)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    add_file_to_resource(res, file_to_upload, check_target_folder=True)
    assert res.files.count() == 2
    # moving the logan.vrt file into mi_folder
    src_path = 'data/contents/{}'.format(single_file_name)
    tgt_path = 'data/contents/{}/{}'.format(mi_folder, single_file_name)

    move_or_rename_file_or_folder(user, res.short_id, src_path, tgt_path)
    assert res.files.count() == 2
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert mi_aggr.files.count() == 2
    assert mi_aggr.metadata.is_dirty
    assert not res.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_move_single_file_out_of_model_instance_aggregation(composite_resource, mock_irods):
    """ test that when we move a file out of a folder that represents a
    model instance aggregation the moved file is no more part of the model instance aggregation"""

    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    mi_folder = 'mi_folder'
    ResourceFile.create_folder(res, mi_folder)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    add_file_to_resource(res, file_to_upload, folder=mi_folder, check_target_folder=True)
    assert res.files.count() == 1
    # upload another file to the resource
    single_file_name = 'logan.vrt'
    file_path = 'pytest/assets/{}'.format(single_file_name)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    add_file_to_resource(res, file_to_upload, folder=mi_folder, check_target_folder=True)
    assert res.files.count() == 2

    # at this point there should not be any model instance aggregation
    assert ModelInstanceLogicalFile.objects.count() == 0
    # set folder to model instance aggregation type
    ModelInstanceLogicalFile.set_file_type(resource=res, user=user, folder_path=mi_folder)
    for res_file in res.files.all():
        assert res_file.has_logical_file
        # file has folder
        assert res_file.file_folder == mi_folder
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # aggregation should have two files
    assert mi_aggr.files.count() == 2

    # moving the logan.vrt file out from mi_folder to the root of the resource
    src_path = 'data/contents/{}/{}'.format(mi_folder, single_file_name)
    tgt_path = 'data/contents/{}'.format(single_file_name)

    move_or_rename_file_or_folder(user, res.short_id, src_path, tgt_path)
    assert res.files.count() == 2
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # aggregation should have only one file
    assert mi_aggr.files.count() == 1
    assert mi_aggr.metadata.is_dirty
    assert not res.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_move_folder_into_model_instance_aggregation(composite_resource, mock_irods):
    """ test that when we move a folder into a folder that represents a
    model instance aggregation the files in the moved folder become part of the model instance aggregation"""

    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    mi_folder = 'mi_folder'
    ResourceFile.create_folder(res, mi_folder)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    add_file_to_resource(res, file_to_upload, folder=mi_folder, check_target_folder=True)
    assert res.files.count() == 1
    # at this point there should not be any model instance aggregation
    assert ModelInstanceLogicalFile.objects.count() == 0
    # set folder to model instance aggregation type
    ModelInstanceLogicalFile.set_file_type(resource=res, user=user, folder_path=mi_folder)
    res_file = res.files.first()
    assert res_file.has_logical_file
    # file has folder
    assert res_file.file_folder == mi_folder
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert mi_aggr.files.count() == 1
    # upload another file to the resource to a different folder
    normal_folder = 'normal_folder'
    ResourceFile.create_folder(res, normal_folder)
    single_file_name = 'logan.vrt'
    file_path = 'pytest/assets/{}'.format(single_file_name)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    add_file_to_resource(res, file_to_upload, folder=normal_folder, check_target_folder=True)
    assert res.files.count() == 2
    # moving normal_folder into mi_folder
    src_path = 'data/contents/{}'.format(normal_folder)
    tgt_path = 'data/contents/{}/{}'.format(mi_folder, normal_folder)

    move_or_rename_file_or_folder(user, res.short_id, src_path, tgt_path)
    assert res.files.count() == 2
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert mi_aggr.files.count() == 2
    assert mi_aggr.metadata.is_dirty
    assert not res.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_move_folder_out_of_model_instance_aggregation(composite_resource, mock_irods):
    """ test that when we move a folder out of a folder that represents a
    model instance aggregation the files in the moved folder are no mare part of the model instance aggregation"""

    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    mi_folder = 'mi_folder'
    ResourceFile.create_folder(res, mi_folder)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    add_file_to_resource(res, file_to_upload, folder=mi_folder, check_target_folder=True)
    # upload another file to the resource to a different folder
    normal_folder = 'normal_folder'
    sub_folder_path = os.path.join(mi_folder, normal_folder)
    ResourceFile.create_folder(res, sub_folder_path)
    single_file_name = 'logan.vrt'
    file_path = 'pytest/assets/{}'.format(single_file_name)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    add_file_to_resource(res, file_to_upload, folder=sub_folder_path, check_target_folder=True)
    assert res.files.count() == 2
    # at this point there should not be any model instance aggregation
    assert ModelInstanceLogicalFile.objects.count() == 0
    # set folder to model instance aggregation type
    ModelInstanceLogicalFile.set_file_type(resource=res, user=user, folder_path=mi_folder)
    for res_file in res.files.all():
        assert res_file.has_logical_file
        # file has folder
        assert res_file.file_folder != ""

    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # aggregation should have two files
    assert mi_aggr.files.count() == 2

    # moving normal_folder out of mi_folder
    src_path = 'data/contents/{}/{}'.format(mi_folder, normal_folder)
    tgt_path = 'data/contents/{}'.format(normal_folder)

    move_or_rename_file_or_folder(user, res.short_id, src_path, tgt_path)
    assert res.files.count() == 2
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that the aggregation has only one file
    assert mi_aggr.files.count() == 1
    assert mi_aggr.metadata.is_dirty
    assert not res.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_update_spatial_coverage_from_children(composite_resource_with_mi_aggregation_folder, mock_irods):
    """Here we are testing fileset level spatial coverage update using the spatial data from the
    contained (children) aggregations - two child aggregations"""

    resource, user = composite_resource_with_mi_aggregation_folder
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # model aggr should not have any spatial coverage
    assert mi_aggr.metadata.spatial_coverage is None
    # auto create a raster aggregation inside the model instance aggregation
    assert GeoRasterLogicalFile.objects.count() == 0
    # upload a raster file to the mi_aggr_path - folder that represents the model instance aggregation
    raster_file_name = 'small_logan.tif'
    raster_file_path = 'hs_file_types/tests/{}'.format(raster_file_name)
    _add_files_to_resource(resource=resource, files_to_add=[raster_file_path], upload_folder=mi_aggr.folder)

    # there should be three resource files ( one extra vrt file added as part of raster aggregation creation)
    assert resource.files.all().count() == 3

    # there should be one raster aggregation now
    assert GeoRasterLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # model aggr should now have spatial coverage
    assert mi_aggr.metadata.spatial_coverage is not None
    assert mi_aggr.metadata.spatial_coverage.value['northlimit'] == 42.050026959773426
    assert mi_aggr.metadata.spatial_coverage.value['eastlimit'] == -111.57773718106199
    assert mi_aggr.metadata.spatial_coverage.value['southlimit'] == 41.98722286030317
    assert mi_aggr.metadata.spatial_coverage.value['westlimit'] == -111.6975629308406

    # auto create a netcdf aggregation inside the model instance aggregation
    assert NetCDFLogicalFile.objects.count() == 0
    # upload a netcdf file to the folder that represents the model instance aggregation
    nc_file_name = "netcdf_valid.nc"
    netcdf_file_path = "hs_file_types/tests/{}".format(nc_file_name)
    _add_files_to_resource(resource=resource, files_to_add=[netcdf_file_path], upload_folder=mi_aggr.folder)
    assert NetCDFLogicalFile.objects.count() == 1
    nc_aggr = NetCDFLogicalFile.objects.first()
    # netcdf aggr should have spatial coverage
    assert nc_aggr.metadata.spatial_coverage is not None

    # update model instance aggregation spatial coverage from the contained 2 aggregations
    mi_aggr.update_spatial_coverage()
    # test model instance aggregation spatial coverage data
    assert mi_aggr.metadata.spatial_coverage.value['northlimit'] == 42.050026959773426
    assert mi_aggr.metadata.spatial_coverage.value['eastlimit'] == -111.5059403684569
    assert mi_aggr.metadata.spatial_coverage.value['southlimit'] == 41.86390807452128
    assert mi_aggr.metadata.spatial_coverage.value['westlimit'] == -111.6975629308406
    assert not resource.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_no_auto_update_spatial_coverage_from_children(composite_resource_with_mi_aggregation_folder, mock_irods):
    """Here we are testing model instance level spatial coverage auto update does not happen when
    a contained aggregation spatial coverage gets created as part of that aggregation creation
    since the  model instance aggregation has spatial coverage prior to the child aggregation
    creation
    """

    resource, user = composite_resource_with_mi_aggregation_folder
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # model aggr should not have any spatial coverage
    assert mi_aggr.metadata.spatial_coverage is None
    # create spatial coverage for model instance
    value_dict = {'east': '56.45678', 'north': '12.6789', 'units': 'Decimal degree'}
    mi_aggr.metadata.create_element('coverage', type='point', value=value_dict)
    # model aggr should now have any spatial coverage
    assert mi_aggr.metadata.spatial_coverage is not None

    # auto create a raster aggregation inside the model instance aggregation
    assert GeoRasterLogicalFile.objects.count() == 0
    # upload a raster file to the mi_aggr_path - folder that represents the model instance aggregation
    raster_file_name = 'small_logan.tif'
    raster_file_path = 'hs_file_types/tests/{}'.format(raster_file_name)
    _add_files_to_resource(resource=resource, files_to_add=[raster_file_path], upload_folder=mi_aggr.folder)

    # there should be three resource files ( one extra vrt file added as part of raster aggregation creation)
    assert resource.files.all().count() == 3

    # there should be one raster aggregation now
    assert GeoRasterLogicalFile.objects.count() == 1
    gr_aggr = GeoRasterLogicalFile.objects.first()
    # raster aggr should have spatial coverage
    assert gr_aggr.metadata.spatial_coverage is not None
    assert gr_aggr.metadata.spatial_coverage.value['northlimit'] == 42.050026959773426
    assert gr_aggr.metadata.spatial_coverage.value['eastlimit'] == -111.57773718106199
    assert gr_aggr.metadata.spatial_coverage.value['southlimit'] == 41.98722286030317
    assert gr_aggr.metadata.spatial_coverage.value['westlimit'] == -111.6975629308406
    # check model instance spatial coverage has not been updated
    assert mi_aggr.metadata.spatial_coverage.value['east'] == value_dict['east']
    assert mi_aggr.metadata.spatial_coverage.value['north'] == value_dict['north']
    assert not resource.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_auto_update_temporal_coverage_from_children(composite_resource_with_mi_aggregation_folder, mock_irods):
    """Here we are testing model instance level temporal coverage auto update when
    a contained aggregation temporal coverage gets created as part of that aggregation creation
    provided the model instance aggregation has no temporal coverage prior to the child aggregation
    creation
    """

    resource, user = composite_resource_with_mi_aggregation_folder
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # model aggr should not have any temporal coverage
    assert mi_aggr.metadata.temporal_coverage is None
    # auto create a netcdf aggregation inside the model instance aggregation
    assert NetCDFLogicalFile.objects.count() == 0
    # upload a netcdf file to the folder that represents the model instance aggregation
    nc_file_name = "netcdf_valid.nc"
    netcdf_file_path = "hs_file_types/tests/{}".format(nc_file_name)
    _add_files_to_resource(resource=resource, files_to_add=[netcdf_file_path], upload_folder=mi_aggr.folder)
    assert NetCDFLogicalFile.objects.count() == 1
    nc_aggr = NetCDFLogicalFile.objects.first()
    # netcdf aggr should have temporal coverage
    assert nc_aggr.metadata.temporal_coverage is not None
    # model aggr should now have temporal coverage
    assert mi_aggr.metadata.temporal_coverage is not None
    # temporal coverage of the model instance aggregation should match with that of the contained
    # netcdf aggregation
    for temp_date in ('start', 'end'):
        assert mi_aggr.metadata.temporal_coverage.value[temp_date] == \
            nc_aggr.metadata.temporal_coverage.value[temp_date]

    assert not resource.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_no_auto_update_temporal_coverage_from_children(composite_resource_with_mi_aggregation_folder, mock_irods):
    """Here we are testing model instance level temporal coverage auto update does not happen when
    a contained aggregation temporal coverage gets created as part of that aggregation creation
    since the  model instance aggregation has temporal coverage prior to the child aggregation
    creation
    """

    resource, user = composite_resource_with_mi_aggregation_folder
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # model aggr should not have any temporal coverage
    assert mi_aggr.metadata.temporal_coverage is None
    # create temporal coverage for model instance
    value_dict = {'name': 'Name for period coverage', 'start': '1/1/2018', 'end': '12/12/2018'}
    mi_aggr.metadata.create_element('coverage', type='period', value=value_dict)
    # model aggr should now have temporal coverage
    assert mi_aggr.metadata.temporal_coverage is not None
    # auto create a netcdf aggregation inside the model instance aggregation
    assert NetCDFLogicalFile.objects.count() == 0
    # upload a netcdf file to the folder that represents the model instance aggregation
    nc_file_name = "netcdf_valid.nc"
    netcdf_file_path = "hs_file_types/tests/{}".format(nc_file_name)
    _add_files_to_resource(resource=resource, files_to_add=[netcdf_file_path], upload_folder=mi_aggr.folder)
    assert NetCDFLogicalFile.objects.count() == 1
    nc_aggr = NetCDFLogicalFile.objects.first()
    # netcdf aggr should have temporal coverage
    assert nc_aggr.metadata.temporal_coverage is not None

    # temporal coverage of the model instance aggregation should NOT match with that of the contained
    # netcdf aggregation
    for temp_date in ('start', 'end'):
        assert mi_aggr.metadata.temporal_coverage.value[temp_date] != \
            nc_aggr.metadata.temporal_coverage.value[temp_date]

    assert not resource.dangling_aggregations_exist()


@pytest.mark.django_db(transaction=True)
def test_update_temporal_coverage_from_children(composite_resource_with_mi_aggregation_folder, mock_irods):
    """Here we are testing model instance level temporal coverage can be updated by user if the contained
    aggregations have temporal coverage
    """

    resource, user = composite_resource_with_mi_aggregation_folder
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # model aggr should not have any temporal coverage
    assert mi_aggr.metadata.temporal_coverage is None
    # create temporal coverage for model instance
    value_dict = {'name': 'Name for period coverage', 'start': '1/1/2018', 'end': '12/12/2018'}
    mi_aggr.metadata.create_element('coverage', type='period', value=value_dict)
    # model aggr should now have temporal coverage
    assert mi_aggr.metadata.temporal_coverage is not None
    # auto create a netcdf aggregation inside the model instance aggregation
    assert NetCDFLogicalFile.objects.count() == 0
    # upload a netcdf file to the folder that represents the model instance aggregation
    nc_file_name = "netcdf_valid.nc"
    netcdf_file_path = "hs_file_types/tests/{}".format(nc_file_name)
    _add_files_to_resource(resource=resource, files_to_add=[netcdf_file_path], upload_folder=mi_aggr.folder)
    assert NetCDFLogicalFile.objects.count() == 1
    nc_aggr = NetCDFLogicalFile.objects.first()
    # netcdf aggr should have temporal coverage
    assert nc_aggr.metadata.temporal_coverage is not None

    # temporal coverage of the model instance aggregation should NOT match with that of the contained
    # netcdf aggregation
    for temp_date in ('start', 'end'):
        assert mi_aggr.metadata.temporal_coverage.value[temp_date] != \
            nc_aggr.metadata.temporal_coverage.value[temp_date]

    # update temporal coverage for model instance from contained aggregations
    mi_aggr.update_temporal_coverage()
    # temporal coverage of the model instance aggregation should now match with that of the contained
    # netcdf aggregation
    for temp_date in ('start', 'end'):
        assert mi_aggr.metadata.temporal_coverage.value[temp_date] == \
            nc_aggr.metadata.temporal_coverage.value[temp_date]

    assert not resource.dangling_aggregations_exist()


def _add_files_to_resource(resource, files_to_add, upload_folder=None):
    files_to_upload = []
    for fl in files_to_add:
        file_to_upload = UploadedFile(file=open(fl, 'rb'), name=os.path.basename(fl))
        files_to_upload.append(file_to_upload)
    added_resource_files = add_resource_files(resource.short_id,
                                              *files_to_upload, folder=upload_folder)
    return added_resource_files
