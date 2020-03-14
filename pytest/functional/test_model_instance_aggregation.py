import os

import pytest
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import UploadedFile

from hs_access_control.models import PrivilegeCodes
from hs_core.hydroshare import add_file_to_resource, ResourceFile
from hs_core.views.utils import move_or_rename_file_or_folder
from hs_file_types.models import ModelInstanceLogicalFile, ModelProgramLogicalFile


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
    upload_folder = None
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
    mi_aggr.set_link_to_model_program(user=user, model_prog_aggr=mp_aggr)
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is related to model program aggregation
    assert mi_aggr.metadata.executed_by is not None


@pytest.mark.django_db(transaction=True)
def test_link_model_aggregations_different_resources(composite_resource_with_mi_aggregation,
                                                     composite_resource_2_with_mp_aggregation, mock_irods):
    """Test that we can link one model instance aggregation in one resource to one model program aggregation
    in another resource provided the user doing the link operation has at edit permission on the resource
    containing the model instance aggregation and view permission on the resource containing the model program
    aggregation"""

    mi_res, mi_user = composite_resource_with_mi_aggregation
    mp_res, mp_user = composite_resource_2_with_mp_aggregation
    assert mi_res != mp_res
    assert mi_user != mp_user

    authorized = mi_user.uaccess.can_change_resource(mi_res)
    assert authorized
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert ModelProgramLogicalFile.objects.count() == 1
    mp_aggr = ModelProgramLogicalFile.objects.first()
    # check that mi_aggr is not related to any model program aggregation
    assert mi_aggr.metadata.executed_by is None
    # test that when the user does not have view access to the mp_res, trying to link the
    # 2 aggregations should fail
    authorized = mi_user.uaccess.can_view_resource(mp_res)
    assert not authorized
    with pytest.raises(PermissionDenied):
        mi_aggr.set_link_to_model_program(user=mi_user, model_prog_aggr=mp_aggr)
    # give mi_user view access to mp_res
    mp_user.uaccess.share_resource_with_user(mp_res, mi_user, PrivilegeCodes.VIEW)
    authorized = mi_user.uaccess.can_view_resource(mp_res)
    assert authorized
    # now we should be able to link model instance aggregation to model program aggregation
    mi_aggr.set_link_to_model_program(user=mi_user, model_prog_aggr=mp_aggr)
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is related to model program aggregation
    assert mi_aggr.metadata.executed_by is not None
    # need to delete this resource as the fixture does not delete it
    mp_res.delete()


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
    upload_folder = None
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
    mi_aggr.set_link_to_model_program(user=user, model_prog_aggr=mp_aggr)
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is related to model program aggregation
    assert mi_aggr.metadata.executed_by is not None
    assert mi_aggr.metadata.is_dirty is False
    # remove/delete mp_aggregation
    mp_aggr.remove_aggregation()
    assert ModelProgramLogicalFile.objects.count() == 0
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is not related to any model program aggregation
    assert mi_aggr.metadata.executed_by is None
    # check that mi_aggr metadata is set to dirty
    assert mi_aggr.metadata.is_dirty is True


@pytest.mark.django_db(transaction=True)
def test_model_instance_on_model_program_resource_delete(composite_resource_with_mi_aggregation,
                                                         composite_resource_2_with_mp_aggregation, mock_irods):
    """Test that when we delete a resource containing a model program aggregation linked to a model
    instance aggregation, the model instance aggregation doesn't get deleted"""

    mi_res, mi_user = composite_resource_with_mi_aggregation
    mp_res, mp_user = composite_resource_2_with_mp_aggregation
    assert mi_res != mp_res
    assert mi_user != mp_user

    authorized = mi_user.uaccess.can_change_resource(mi_res)
    assert authorized
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert ModelProgramLogicalFile.objects.count() == 1
    mp_aggr = ModelProgramLogicalFile.objects.first()
    # check that mi_aggr is not related to any model program aggregation
    assert mi_aggr.metadata.executed_by is None
    # give mi_user view access to mp_res
    mp_user.uaccess.share_resource_with_user(mp_res, mi_user, PrivilegeCodes.VIEW)
    authorized = mi_user.uaccess.can_view_resource(mp_res)
    assert authorized
    # now we should be able to link model instance aggregation to model program aggregation
    mi_aggr.set_link_to_model_program(user=mi_user, model_prog_aggr=mp_aggr)
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is related to model program aggregation
    assert mi_aggr.metadata.executed_by is not None
    assert mi_aggr.metadata.is_dirty is False
    # delete mp_resource
    mp_res.delete()
    assert ModelProgramLogicalFile.objects.count() == 0
    # check that mi_aggr is not related to any model program aggregation
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert mi_aggr.metadata.executed_by is None
    assert mi_aggr.metadata.is_dirty is True


@pytest.mark.django_db(transaction=True)
def test_model_instance_on_model_program_rename_1(composite_resource_with_mi_aggregation, mock_irods):
    """Test that when we rename a file that represents a model program aggregation then the inked model instance
    aggregation metadata is set to dirty"""

    res, user = composite_resource_with_mi_aggregation
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is not related to any model program aggregation
    assert mi_aggr.metadata.executed_by is None
    # create a model program aggregation
    file_path = 'pytest/assets/logan.vrt'
    upload_folder = None
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
    mi_aggr.set_link_to_model_program(user=user, model_prog_aggr=mp_aggr)
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is related to model program aggregation
    assert mi_aggr.metadata.executed_by is not None
    assert mi_aggr.metadata.is_dirty is False
    # rename the model program file name
    src_path = 'data/contents/{}'.format(res_file.file_name)
    tgt_path = 'data/contents/{}'.format("logan_1.vrt")
    move_or_rename_file_or_folder(user, res.short_id, src_path, tgt_path)
    assert ModelProgramLogicalFile.objects.count() == 1
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr metadata is set to dirty
    assert mi_aggr.metadata.is_dirty is True


@pytest.mark.django_db(transaction=True)
def test_model_instance_on_model_program_rename_2(composite_resource_with_mi_aggregation, mock_irods):
    """Test that when we rename a folder that represents a model program aggregation then the inked model instance
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
    mi_aggr.set_link_to_model_program(user=user, model_prog_aggr=mp_aggr)
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr is related to model program aggregation
    assert mi_aggr.metadata.executed_by is not None
    assert mi_aggr.metadata.is_dirty is False
    # rename the model program file name
    src_path = 'data/contents/{}'.format(mp_folder)
    tgt_path = 'data/contents/{}'.format("{}_1".format(mp_folder))
    move_or_rename_file_or_folder(user, res.short_id, src_path, tgt_path)
    assert ModelProgramLogicalFile.objects.count() == 1
    assert ModelInstanceLogicalFile.objects.count() == 1
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    # check that mi_aggr metadata is set to dirty
    assert mi_aggr.metadata.is_dirty is True


@pytest.mark.django_db(transaction=True)
def test_set_metadata(composite_resource_with_mi_aggregation, mock_irods):
    """Test that we can store all metadata items for a model instance aggregation"""

    res, user = composite_resource_with_mi_aggregation
    # mi_aggr = next(res.logical_files)
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
