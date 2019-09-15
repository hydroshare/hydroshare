import os

import pytest
from django.core.files.uploadedfile import UploadedFile

from hs_core.hydroshare import add_file_to_resource
from hs_file_types.models import ModelProgramLogicalFile


@pytest.mark.django_db(transaction=True)
def test_create_aggregation_from_file(composite_resource):
    """test that we can create a model program aggregation from a single file"""

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



