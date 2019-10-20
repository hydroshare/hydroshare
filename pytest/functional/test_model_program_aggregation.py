import os
from dateutil import parser
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
    assert mp_aggregation.dataset_name == 'generic_file'


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
    assert mp_aggregation.dataset_name == 'generic_file'


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
    assert mp_aggregation.dataset_name == new_folder


@pytest.mark.django_db(transaction=True)
def test_upload_file_to_aggregation_folder(composite_resource, mock_irods):
    """test that when we upload a file to a model program aggregation folder that file becomes part of the
    aggregation"""

    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    new_folder = 'mp_folder'
    ResourceFile.create_folder(res, new_folder)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    add_file_to_resource(res, file_to_upload, folder=new_folder, check_target_folder=True)
    assert res.files.count() == 1
    # set folder to model program aggregation type
    ModelProgramLogicalFile.set_file_type(resource=res, user=user, folder_path=new_folder)
    assert ModelProgramLogicalFile.objects.count() == 1
    mp_aggregation = ModelProgramLogicalFile.objects.first()
    assert mp_aggregation.files.count() == 1
    assert mp_aggregation.folder == new_folder
    assert mp_aggregation.dataset_name == new_folder
    # add another file to the model program aggregation folder
    file_path = 'pytest/assets/logan.vrt'
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))
    add_file_to_resource(res, file_to_upload, folder=new_folder, check_target_folder=True)
    assert res.files.count() == 2
    for res_file in res.files.all():
        assert res_file.has_logical_file

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
def test_mark_multiple_res_files_as_mp_file_type(composite_resource, mock_irods):
    """test that we can mark more than one resource file that is part of a model program aggregation as a specific
    model program file type (e.g., software)"""

    res, user = composite_resource
    file_path = 'pytest/assets/{}'
    txt_file_path = file_path.format('generic_file.txt')
    vrt_file_path = file_path.format('logan.vrt')
    upload_folder = 'mp_folder'
    ResourceFile.create_folder(res, upload_folder)
    file_to_upload = UploadedFile(file=open(txt_file_path, 'rb'),
                                  name=os.path.basename(txt_file_path))

    res_file_txt = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

    file_to_upload = UploadedFile(file=open(vrt_file_path, 'rb'),
                                  name=os.path.basename(vrt_file_path))
    res_file_vrt = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )
    assert res.files.count() == 2
    # create model program aggregation
    assert ModelProgramLogicalFile.objects.count() == 0
    # set the folder to model program aggregation type
    ModelProgramLogicalFile.set_file_type(res, user, folder_path=upload_folder)
    assert ModelProgramLogicalFile.objects.count() == 1

    assert MPResFileType.objects.count() == 0
    mp_aggregation = ModelProgramLogicalFile.objects.first()
    mp_type = 'software'
    # set the txt file as software for this aggregation
    mp_aggregation.set_res_file_as_mp_file_type(res_file=res_file_txt, mp_file_type=mp_type)
    assert MPResFileType.objects.count() == 1
    # set the vrt file as software for this aggregation
    mp_aggregation.set_res_file_as_mp_file_type(res_file=res_file_vrt, mp_file_type=mp_type)
    assert MPResFileType.objects.count() == 2


@pytest.mark.django_db(transaction=True)
def test_mark_res_file_as_mp_file_type_failure_1(composite_resource, mock_irods):
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


@pytest.mark.django_db(transaction=True)
def test_mark_res_file_as_mp_file_type_failure_2(composite_resource, mock_irods):
    """test that we can't mark the a resource file that is not part of a model program aggregation as one of the
    model program file type"""

    res, user = composite_resource
    file_path = 'pytest/assets/{}'
    txt_file_path = file_path.format('generic_file.txt')
    vrt_file_path = file_path.format('logan.vrt')
    upload_folder = None
    file_to_upload = UploadedFile(file=open(txt_file_path, 'rb'),
                                  name=os.path.basename(txt_file_path))

    res_file_txt = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

    file_to_upload = UploadedFile(file=open(vrt_file_path, 'rb'),
                                  name=os.path.basename(vrt_file_path))
    res_file_vrt = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )
    assert res.files.count() == 2
    # create model program aggregation
    assert ModelProgramLogicalFile.objects.count() == 0
    # set the txt file to model program aggregation type
    ModelProgramLogicalFile.set_file_type(res, user, res_file_txt.id)

    assert MPResFileType.objects.count() == 0
    mp_aggregation = ModelProgramLogicalFile.objects.first()
    # trying set the vrt file as engine for this aggregation should fail as the vrt file is not part of
    # the aggregation
    with pytest.raises(ValidationError):
        mp_aggregation.set_res_file_as_mp_file_type(res_file=res_file_vrt, mp_file_type='engine')

    assert MPResFileType.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_delete_res_file_deletes_mp_file_object(composite_resource_with_mp_aggregation, mock_irods):
    """test that when a res file that is marked as mp file type is deleted then mp file type object also gets
    deleted"""

    res, user = composite_resource_with_mp_aggregation
    mp_aggr = next(res.logical_files)
    assert isinstance(mp_aggr, ModelProgramLogicalFile)
    res_file = res.files.first()
    assert MPResFileType.objects.count() == 0
    mp_aggregation = ModelProgramLogicalFile.objects.first()
    # set the res_file as software for this aggregation
    mp_aggregation.set_res_file_as_mp_file_type(res_file=res_file, mp_file_type='software')
    assert MPResFileType.objects.count() == 1
    # delete res_file
    res_file.delete()
    # mp program file type got deleted
    assert MPResFileType.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_set_schema_json(composite_resource_with_mp_aggregation, mock_irods):
    """test that we can set the mi_schema_json attribute with a valid json schema"""

    res, user = composite_resource_with_mp_aggregation
    mp_aggr = next(res.logical_files)
    assert isinstance(mp_aggr, ModelProgramLogicalFile)
    # no json schema at this point
    assert not mp_aggr.mi_schema_json
    # set mi metadata json schema from the content of the following file
    schema_file_path = 'pytest/assets/mi_schema.json'
    with open(schema_file_path, 'r') as file_obj:
        json_schema = file_obj.read()
    assert len(json_schema) > 0
    mp_aggr.set_mi_schema(json_schema_string=json_schema)
    assert mp_aggr.mi_schema_json


@pytest.mark.django_db(transaction=True)
def test_set_schema_invalid_json(composite_resource_with_mp_aggregation, mock_irods):
    """test that we can't set the mi_schema_json attribute with a an invalid json schema"""

    res, user = composite_resource_with_mp_aggregation
    mp_aggr = next(res.logical_files)
    assert isinstance(mp_aggr, ModelProgramLogicalFile)
    # no json schema at this point
    assert not mp_aggr.mi_schema_json
    # set mi metadata json schema from the content of the following file which should fail
    schema_file_path = 'pytest/assets/mi_schema_invalid.json'
    with open(schema_file_path, 'r') as file_obj:
        json_schema = file_obj.read()
    assert len(json_schema) > 0
    with pytest.raises(ValidationError):
        mp_aggr.set_mi_schema(json_schema_string=json_schema)

    assert not mp_aggr.mi_schema_json


@pytest.mark.django_db(transaction=True)
def test_set_metadata(composite_resource_with_mp_aggregation, mock_irods):
    """Test that we can store all metadata items for a model program aggregation"""

    res, user = composite_resource_with_mp_aggregation
    mp_aggr = next(res.logical_files)
    assert isinstance(mp_aggr, ModelProgramLogicalFile)

    # test extra metadata
    assert not mp_aggr.metadata.extra_metadata
    extra_meta = {'key1': 'value 1', 'key2': 'value 2'}
    mp_aggr.metadata.extra_metadata = extra_meta
    mp_aggr.metadata.save()
    assert mp_aggr.metadata.extra_metadata == extra_meta

    # test keywords
    assert not mp_aggr.metadata.keywords
    keywords = ['kw-1', 'kw-2']
    mp_aggr.metadata.keywords = keywords
    mp_aggr.metadata.save()
    assert mp_aggr.metadata.keywords == keywords

    # test coverage metadata
    assert not mp_aggr.metadata.coverages.all()
    value_dict = {'name': 'Name for period coverage', 'start': '1/1/2000', 'end': '12/12/2012'}
    temp_cov = mp_aggr.metadata.create_element('coverage', type='period', value=value_dict)
    assert temp_cov.value['name'] == 'Name for period coverage'
    assert temp_cov.value['start'] == '1/1/2000'
    assert temp_cov.value['end'] == '12/12/2012'
    assert mp_aggr.metadata.coverages.all().count() == 1

    value_dict = {'east': '56.45678', 'north': '12.6789', 'units': 'Decimal degree'}
    spatial_cov = mp_aggr.metadata.create_element('coverage', type='point', value=value_dict)
    assert spatial_cov.value['projection'] == 'WGS 84 EPSG:4326'
    assert spatial_cov.value['units'] == 'Decimal degree'
    assert spatial_cov.value['north'] == 12.6789
    assert spatial_cov.value['east'] == 56.45678
    assert mp_aggr.metadata.coverages.all().count() == 2
    # test version metadata
    assert not mp_aggr.metadata.version
    mp_aggr.metadata.version = "Ver 1.2.1"
    mp_aggr.metadata.save()
    assert mp_aggr.metadata.version == "Ver 1.2.1"
    # test programming languages metadata
    assert not mp_aggr.metadata.programming_languages
    mp_aggr.metadata.programming_languages = ['C++']
    mp_aggr.metadata.save()
    assert mp_aggr.metadata.programming_languages[0] == 'C++'
    mp_aggr.metadata.programming_languages = ['C++', 'Python']
    mp_aggr.metadata.save()
    assert mp_aggr.metadata.programming_languages == ['C++', 'Python']
    # test operating_systems metadata
    assert not mp_aggr.metadata.operating_systems
    mp_aggr.metadata.operating_systems = ['Linux']
    mp_aggr.metadata.save()
    assert mp_aggr.metadata.operating_systems[0] == 'Linux'
    mp_aggr.metadata.operating_systems = ['Linux', 'Windows 10']
    mp_aggr.metadata.save()
    assert mp_aggr.metadata.operating_systems == ['Linux', 'Windows 10']

    # test release date metadata
    assert not mp_aggr.metadata.release_date
    mp_aggr.metadata.release_date = parser.parse('2019-09-22')
    mp_aggr.metadata.save()
    assert mp_aggr.metadata.release_date.date() == parser.parse('2019-09-22').date()

    # test website metadata
    assert not mp_aggr.metadata.website
    mp_aggr.metadata.website = 'https://usu.edu'
    mp_aggr.metadata.save()
    assert mp_aggr.metadata.website == 'https://usu.edu'

    # test code repository metadata
    assert not mp_aggr.metadata.code_repository
    mp_aggr.metadata.code_repository = 'https://github.com/swat'
    mp_aggr.metadata.save()
    assert mp_aggr.metadata.code_repository == 'https://github.com/swat'
