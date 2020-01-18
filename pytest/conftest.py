import os
import json
import uuid

import pytest
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from hs_access_control.models import UserAccess
from hs_core import hydroshare
from hs_core.hydroshare import add_file_to_resource
from hs_labels.models import UserLabels
from hs_file_types.models import ModelProgramLogicalFile, ModelInstanceLogicalFile


@pytest.fixture(scope="function")
def mock_irods():
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
        print(">> irods mock setup")
    yield

    """Stop iRODS patchers."""
    if settings.IRODS_HOST != 'data.local.org':
        for patcher in irods_patchers:
            patcher.stop()
        print(">> irods mock teardown")


@pytest.mark.django_db
@pytest.fixture(scope="function")
def resource_with_metadata():
    """Resource with metadata for testing"""
    rtype = 'GenericResource'
    res_uuid = str(uuid.uuid4())
    title = 'Resource {}'.format(res_uuid)
    metadata = []
    metadata.append({'coverage': {'type': 'period', 'value': {'start': '01/01/2000',
                                                              'end': '12/12/2010'}}})
    statement = 'This resource is shared under the Creative Commons Attribution CC BY.'
    url = 'http://creativecommons.org/licenses/by/4.0/'
    metadata.append({'rights': {'statement': statement, 'url': url}})
    metadata.append({'language': {'code': 'fre'}})

    # contributor
    con_name = 'Mike Sundar'
    con_org = "USU"
    con_email = 'mike.sundar@usu.edu'
    con_address = "11 River Drive, Logan UT-84321, USA"
    con_phone = '435-567-0989'
    con_homepage = 'http://usu.edu/homepage/001'
    con_identifiers = {'ORCID': 'https://orcid.org/mike_s',
                       'ResearchGateID': 'https://www.researchgate.net/mike_s'}
    metadata.append({'contributor': {'name': con_name,
                                     'organization': con_org, 'email': con_email,
                                     'address': con_address, 'phone': con_phone,
                                     'homepage': con_homepage,
                                     'identifiers': con_identifiers}})

    # creator
    cr_name = 'John Smith'
    cr_org = "USU"
    cr_email = 'jsmith@gmail.com'
    cr_address = "101 Clarson Ave, Provo UT-84321, USA"
    cr_phone = '801-567=9090'
    cr_homepage = 'http://byu.edu/homepage/002'
    cr_identifiers = {'ORCID': 'https://orcid.org/john_smith',
                      'ResearchGateID': 'https://www.researchgate.net/john_smith'}
    metadata.append({'creator': {'name': cr_name, 'organization': cr_org,
                                 'email': cr_email, 'address': cr_address,
                                 'phone': cr_phone, 'homepage': cr_homepage,
                                 'identifiers': cr_identifiers}})

    # relation
    metadata.append({'relation': {'type': 'isPartOf',
                                  'value': 'http://hydroshare.org/resource/001'}})
    # source
    metadata.append({'source': {'derived_from': 'http://hydroshare.org/resource/0001'}})

    # identifier
    metadata.append({'identifier': {'name': 'someIdentifier', 'url': 'http://some.org/001'}})

    # fundingagency
    agency_name = 'NSF'
    award_title = "Cyber Infrastructure"
    award_number = "NSF-101-20-6789"
    agency_url = "http://www.nsf.gov"
    metadata.append({'fundingagency': {'agency_name': agency_name, 'award_title': award_title,
                                       'award_number': award_number, 'agency_url': agency_url}})

    user = User.objects.get(username='admin')

    user_access = UserAccess(user=user)
    user_access.save()
    user_labels = UserLabels(user=user)
    user_labels.save()

    metadata = json.loads(json.dumps(metadata))

    _res = hydroshare.create_resource(
        resource_type=rtype,
        owner=user,
        title=title,
        metadata=metadata,
        files=(open('pytest/assets/cea.tif'),)
    )
    yield res_uuid
    _res.delete()


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
def composite_resource_with_mp_aggregation(composite_resource):
    res, user = composite_resource
    file_path = 'pytest/assets/generic_file.txt'
    upload_folder = None
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
    upload_folder = None
    file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                  name=os.path.basename(file_path))

    res_file = add_file_to_resource(
        res, file_to_upload, folder=upload_folder, check_target_folder=True
    )

    # set file to model instance aggregation type
    ModelInstanceLogicalFile.set_file_type(res, user, res_file.id)
    yield res, user
