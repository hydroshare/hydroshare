import os

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from hs_core.hydroshare import add_file_to_resource, ResourceFile
from hs_file_types.models import ModelProgramLogicalFile
from hs_file_types.models import ModelProgramResourceFileType as MPResFileType


@pytest.mark.django_db(transaction=True)
def test_create_aggregation_from_file_1(composite_resource, mock_irods):
    """test that we can create a model program aggregation from a single file that exists at root"""

    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    upload_folder = None
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )
    assert res.files.count() == 1
    # create model program aggregation
    assert ModelProgramLogicalFile.objects.count() == 0
    # set file to model program aggregation type
    ModelProgramLogicalFile.set_file_type(res, user, res_file.id)
    res_file = res.files.first()
    assert res_file.has_logical_file
    # file has no folder
    assert res_file.file_folder is None
    assert ModelProgramLogicalFile.objects.count() == 1
    mp_aggregation = ModelProgramLogicalFile.objects.first()
    assert mp_aggregation.files.count() == 1


@pytest.mark.django_db(transaction=True)
def test_create_aggregation_from_file_2(composite_resource, mock_irods):
    """test that we can create a model program aggregation from a single file that exists in a folder"""

    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    new_folder = 'mp_folder'
    ResourceFile.create_folder(res, new_folder)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    res_file = add_file_to_resource(
        res, file_to_upload, folder=new_folder, check_target_folder=True
    )
    assert res.files.count() == 1
    # create model program aggregation
    assert ModelProgramLogicalFile.objects.count() == 0
    # set file to model program aggregation type
    ModelProgramLogicalFile.set_file_type(res, user, res_file.id)
    res_file = res.files.first()
    assert res_file.has_logical_file
    # file has folder
    assert res_file.file_folder == new_folder
    assert ModelProgramLogicalFile.objects.count() == 1
    mp_aggregation = ModelProgramLogicalFile.objects.first()
    assert mp_aggregation.files.count() == 1


@pytest.mark.django_db(transaction=True)
def test_create_aggregation_from_folder(composite_resource, mock_irods):
    """test that we can create a model program aggregation from a folder that contains a resource file"""

    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    new_folder = 'mp_folder'
    ResourceFile.create_folder(res, new_folder)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    add_file_to_resource(res, file_to_upload, folder=new_folder, check_target_folder=True)
    assert res.files.count() == 1
    # at this point there should not be any model program aggregation
    assert ModelProgramLogicalFile.objects.count() == 0
    # set folder to model program aggregation type
    ModelProgramLogicalFile.set_file_type(resource=res, user=user, folder_path=new_folder)
    res_file = res.files.first()
    assert res_file.has_logical_file
    # file has folder
    assert res_file.file_folder == new_folder
    assert ModelProgramLogicalFile.objects.count() == 1
    mp_aggregation = ModelProgramLogicalFile.objects.first()
    assert mp_aggregation.files.count() == 1
    assert mp_aggregation.folder == new_folder


@pytest.mark.django_db(transaction=True)
def test_create_aggregation_from_folder_failure(composite_resource, mock_irods):
    """test that we can't create a model program aggregation from a folder that does not contain any resource file"""

    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    new_folder = 'mp_folder'
    ResourceFile.create_folder(res, new_folder)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    add_file_to_resource(res, file_to_upload, folder=None, check_target_folder=True)
    assert res.files.count() == 1
    # create model program aggregation
    assert ModelProgramLogicalFile.objects.count() == 0
    # setting folder to model program aggregation type should fail
    with pytest.raises(ValidationError):
        ModelProgramLogicalFile.set_file_type(resource=res, user=user, folder_path=new_folder)

    res_file = res.files.first()
    # file has no logical file
    assert not res_file.has_logical_file
    # file has no folder
    assert res_file.file_folder is None
    # no model program logical file object was created
    assert ModelProgramLogicalFile.objects.count() == 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('mp_type', ['software', 'engine', 'documentation', 'release notes'])
def test_mark_res_file_as_mp_file_type(composite_resource, mp_type, mock_irods):
    """test that we can mark a resource file that is part of a model program aggregation as one of the model program
    file types"""

    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    upload_folder = None
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )
    assert res.files.count() == 1
    # create model program aggregation
    assert ModelProgramLogicalFile.objects.count() == 0
    # set file to model program aggregation type
    ModelProgramLogicalFile.set_file_type(res, user, res_file.id)
    res_file = res.files.first()
    assert MPResFileType.objects.count() == 0
    mp_aggregation = ModelProgramLogicalFile.objects.first()
    # set the res_file as software for this aggregation
    mp_aggregation.set_res_file_as_mp_file_type(res_file=res_file, mp_file_type=mp_type)

    assert MPResFileType.objects.count() == 1
    mp_res_file_type = MPResFileType.objects.first()
    assert mp_res_file_type.res_file.short_path == res_file.short_path
    assert mp_res_file_type.file_type == MPResFileType.type_from_string(mp_type)


@pytest.mark.django_db(transaction=True)
def test_mark_res_file_as_mp_file_type_failure(composite_resource, mock_irods):
    """test that we can't mark the same resource file that is part of a model program aggregation as one of the
    model program file type twice"""

    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    upload_folder = None
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )
    assert res.files.count() == 1
    # create model program aggregation
    assert ModelProgramLogicalFile.objects.count() == 0
    # set file to model program aggregation type
    ModelProgramLogicalFile.set_file_type(res, user, res_file.id)
    res_file = res.files.first()
    assert MPResFileType.objects.count() == 0
    mp_aggregation = ModelProgramLogicalFile.objects.first()
    # set the res_file as software for this aggregation
    mp_aggregation.set_res_file_as_mp_file_type(res_file=res_file, mp_file_type='software')

    assert MPResFileType.objects.count() == 1
    mp_res_file_type = MPResFileType.objects.first()
    assert mp_res_file_type.res_file.short_path == res_file.short_path
    assert mp_res_file_type.file_type == MPResFileType.type_from_string('software')
    # trying to set the same file again as mp file type should fail
    with pytest.raises(ValidationError):
        mp_aggregation.set_res_file_as_mp_file_type(res_file=res_file, mp_file_type='engine')

    assert MPResFileType.objects.count() == 1
