import json
import os
import uuid

import pytest
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import UploadedFile

from hs_access_control.models import UserAccess
from hs_core import hydroshare
from hs_core.hydroshare import add_file_to_resource, ResourceFile
from hs_file_types.models import ModelProgramLogicalFile, ModelInstanceLogicalFile
from hs_labels.models import UserLabels


@pytest.fixture(scope="module")
def mock_irods():
    # only mock up testing iRODS operations when local iRODS container is not used
    if settings.IRODS_HOST != 'data.local.org':
        from mock import patch

        irods_patchers = (
            patch("hs_core.hydroshare.hs_bagit.delete_files_and_bag"),
            patch("hs_core.hydroshare.hs_bagit.create_bag"),
            patch("hs_core.hydroshare.hs_bagit.create_bag_files"),
            patch("hs_core.tasks.create_bag_by_irods"),
            patch("hs_core.hydroshare.utils.copy_resource_files_and_AVUs"),
        )

        for patcher in irods_patchers:
            patcher.start()
    yield

    """Stop iRODS patchers."""
    if settings.IRODS_HOST != 'data.local.org':
        for patcher in irods_patchers:
            patcher.stop()


def base_sample_resource(username='admin', title=str(uuid.uuid4()), contributor=str(uuid.uuid4()),
                         creator=str(uuid.uuid4())):
    """A resource with sample entries that can be customized by tests"""
    rtype = 'CompositeResource'
    metadata = [{'coverage': {'type': 'period', 'value': {'start': '01/01/2000',
                                                          'end': '12/12/2010'}}}]
    statement = 'This resource is shared under the Creative Commons Attribution CC BY.'
    url = 'http://creativecommons.org/licenses/by/4.0/'
    metadata.append({'rights': {'statement': statement, 'url': url}})
    metadata.append({'language': {'code': 'fre'}})

    # contributor
    con_name = contributor
    con_org = 'USU'
    con_email = 'mike.sundar@usu.edu'
    con_address = "11 River Drive, Logan UT-84321, USA"
    con_phone = '435-567-0989'
    con_homepage = 'http://usu.edu/homepage/001'
    con_identifiers = {'ORCID': 'https://orcid.org/0000-0003-4621-0559',
                       'ResearchGateID': 'https://www.researchgate.net/profile/mike_s'}
    metadata.append({'contributor': {'name': con_name,
                                     'organization': con_org, 'email': con_email,
                                     'address': con_address, 'phone': con_phone,
                                     'homepage': con_homepage,
                                     'identifiers': con_identifiers}})

    # creator
    cr_name = creator
    cr_org = 'USU'
    cr_email = 'jsmith@gmail.com'
    cr_address = "101 Clarson Ave, Provo UT-84321, USA"
    cr_phone = '801-567=9090'
    cr_homepage = 'http://byu.edu/homepage/002'
    cr_identifiers = {'ORCID': 'https://orcid.org/0000-0003-4621-0559',
                      'ResearchGateID': 'https://www.researchgate.net/profile/john_smith'}
    metadata.append({'creator': {'name': cr_name, 'organization': cr_org,
                                 'email': cr_email, 'address': cr_address,
                                 'phone': cr_phone, 'homepage': cr_homepage,
                                 'identifiers': cr_identifiers}})

    # relation
    metadata.append({'relation': {'type': 'isPartOf',
                                  'value': 'http://hydroshare.org/resource/001'}})

    # geospatialrelation
    metadata.append({'geospatialrelation': {'type': 'relation',
                                            'value': 'https://geoconnex.us/ref/dams/1083460',
                                            'text': 'Bonnie Meade [dams/1083460]'}})

    # identifier
    # metadata.append({'identifier': {'name': 'someIdentifier', 'url': 'http://some.org/001'}})

    # fundingagency
    agency_name = 'NSF'
    award_title = "Cyber Infrastructure"
    award_number = "NSF-101-20-6789"
    agency_url = "http://www.nsf.gov"
    metadata.append({'fundingagency': {'agency_name': agency_name, 'award_title': award_title,
                                       'award_number': award_number, 'agency_url': agency_url}})

    user = User.objects.get(username=username)

    _ = UserAccess(user=user)  # noqa
    _ = UserLabels(user=user)  # noqa

    metadata = json.loads(json.dumps(metadata))

    _res = hydroshare.create_resource(
        resource_type=rtype,
        owner=user,
        title=title,
        metadata=metadata,
        # files=(open('file.ext', 'rb'),)  # use a file that will exist in all environments and containers
    )
    return _res


@pytest.mark.django_db
@pytest.fixture(scope="function")
def sample_user():
    hydroshare_author_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
    user = hydroshare.create_account(
        '{}@noreply.org'.format(str(uuid.uuid4())),
        username='{}'.format(str(uuid.uuid4())),
        first_name='First',
        last_name='Last',
        superuser=False,
        groups=[]
    )
    yield user
    user.delete()


@pytest.mark.django_db
@pytest.fixture(scope="function")
def public_resource_with_metadata():
    resource = base_sample_resource()
    resource.raccess.public = True
    resource.raccess.discoverable = True
    resource.keywords_string = str(uuid.uuid4())
    resource.raccess.save()  # saves flag, doesn't necessarily re-index
    resource.save()  # invokes re-indexing.
    yield resource  # this is the elegant teardown pattern for PyTest
    resource.delete()


@pytest.mark.django_db
@pytest.fixture(scope="function")
def another_public_resource_with_metadata():
    resource = base_sample_resource(title=str(uuid.uuid4()), creator=str(uuid.uuid4()))
    resource.raccess.public = True
    resource.raccess.discoverable = True
    resource.keywords_string = str(uuid.uuid4())
    resource.raccess.save()  # saves flag, doesn't necessarily re-index
    resource.save()  # invokes re-indexing.
    yield resource  # this is the elegant teardown pattern for PyTest
    resource.delete()


@pytest.mark.django_db
@pytest.fixture(scope="function")
def private_resource_with_metadata(sample_user):
    resource = base_sample_resource(username=sample_user.username)
    resource.keywords_string = str(uuid.uuid4())
    resource.raccess.save()
    resource.save()
    yield resource
    resource.delete()


def create_composite_resource(u_name, u_email, u_lastname, u_firstname, res_title):
    group, _ = Group.objects.get_or_create(name='Hydroshare Author')
    user = hydroshare.create_account(
        u_email,
        username=u_name,
        first_name=u_firstname,
        last_name=u_lastname,
        superuser=False,
        groups=[group]
    )
    _res = hydroshare.create_resource(
        resource_type='CompositeResource',
        owner=user,
        title=res_title,
        metadata=[],
        files=()
    )
    return _res, user


@pytest.mark.django_db
@pytest.fixture(scope="function")
def composite_resource():
    """composite resource for testing"""
    group, _ = Group.objects.get_or_create(name='Hydroshare Author')
    user = hydroshare.create_account(
        'user1@nowhere.com',
        username='user1',
        first_name='Creator_FirstName',
        last_name='Creator_LastName',
        superuser=False,
        groups=[group]
    )
    _res = hydroshare.create_resource(
        resource_type='CompositeResource',
        owner=user,
        title='Test Composite Resource',
        metadata=[],
        files=()
    )

    yield _res, user
    _res.delete()
    user.delete()


@pytest.mark.django_db
@pytest.fixture(scope="function")
def composite_resource_2():
    """composite resource for testing"""
    _res, user = create_composite_resource(u_name='user2', u_email='user2@gmail.com', u_firstname='user2_firstname',
                                           u_lastname='user2_lastname', res_title='Composite Resource-2 for Testing')
    yield _res, user
    # not deleting the resource here as the resource in some test cases needs be deleted as part of the test
    user.delete()


@pytest.mark.django_db
@pytest.fixture(scope="function")
def composite_resource_with_mp_aggregation(composite_resource):
    res, user = composite_resource
    file_path = 'pytest/assets/logan.vrt'
    upload_folder = ''
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

    # set file to model program aggregation type
    ModelProgramLogicalFile.set_file_type(res, user, res_file.id)
    yield res, user


@pytest.mark.django_db
@pytest.fixture(scope="function")
def composite_resource_2_with_mp_aggregation(composite_resource_2):
    res, user = composite_resource_2
    file_path = 'pytest/assets/logan.vrt'
    upload_folder = ''
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

    # set file to model program aggregation type
    ModelProgramLogicalFile.set_file_type(res, user, res_file.id)
    yield res, user


@pytest.mark.django_db
@pytest.fixture(scope="function")
def composite_resource_with_mi_aggregation(composite_resource):
    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    upload_folder = ''
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

    # set file to model instance aggregation type
    ModelInstanceLogicalFile.set_file_type(res, user, res_file.id)
    yield res, user


@pytest.mark.django_db
@pytest.fixture(scope="function")
def composite_resource_with_mi_aggregation_folder(composite_resource):
    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    mi_folder = "mi-folder"
    ResourceFile.create_folder(res, mi_folder)
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    add_file_to_resource(
        res, file_to_upload, folder=mi_folder, check_target_folder=True
    )

    # set the folder to model instance aggregation type
    ModelInstanceLogicalFile.set_file_type(res, user, folder_path=mi_folder)
    yield res, user


@pytest.mark.django_db
@pytest.fixture(scope="function")
def composite_resource_with_mi_mp_aggregation(composite_resource):
    res, user = composite_resource
    # create model instance aggregation
    file_path = 'pytest/assets/generic_file.txt'
    upload_folder = ''
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

    # set file to model instance aggregation type
    ModelInstanceLogicalFile.set_file_type(res, user, res_file.id)

    # create model program aggregation
    file_path = 'pytest/assets/logan.vrt'
    upload_folder = ''
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

    # set file to model program aggregation type
    ModelProgramLogicalFile.set_file_type(res, user, res_file.id)
    yield res, user


@pytest.mark.django_db
@pytest.fixture(scope="function")
def resource_for_citation(sample_user):
    resource = base_sample_resource(username=sample_user.username)
    resource.raccess.save()
    resource.save()
    yield resource
    resource.delete()
