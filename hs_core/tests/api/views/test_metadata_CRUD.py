import json
import os
import shutil
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework import status
from unittest_parametrize import ParametrizedTestCase, parametrize, param

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.testing import MockS3TestCaseMixin, ViewTestCase
from hs_core.views import (
    add_metadata_element,
    delete_metadata_element,
    delete_resource_coverage,
    update_metadata_element,
)


class TestCRUDMetadata(MockS3TestCaseMixin, ParametrizedTestCase, ViewTestCase):
    def setUp(self):
        super(TestCRUDMetadata, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.username = 'john'
        self.password = 'jhmypassword'
        self.user = hydroshare.create_account(
            'john@gmail.com',
            username=self.username,
            first_name='John',
            last_name='Clarson',
            superuser=False,
            password=self.password,
            groups=[]
        )
        self.gen_res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Resource Key/Value Metadata Testing'
        )

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        super(TestCRUDMetadata, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()

    def create_resource(self, resource_type: str = "CompositeResource", title: str = "Test Resource"):
        return hydroshare.create_resource(
            resource_type=resource_type,
            owner=self.user,
            title=title
        )

    def test_CRUD_metadata(self):
        # here we are testing the add_metadata_element view function

        # There should be no keywords (subject element) now
        self.assertEqual(self.gen_res.metadata.subjects.count(), 0)

        # add keywords
        url_params = {'shortkey': self.gen_res.short_id, 'element_name': 'subject'}
        post_data = {'value': 'kw-1, kw 2, key word'}
        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.set_request_message_attributes(request)
        response = add_metadata_element(request, shortkey=self.gen_res.short_id,
                                        element_name='subject')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content.decode())
        self.assertEqual(response_dict['status'], 'success')
        self.assertEqual(response_dict['element_name'], 'subject')
        self.gen_res.refresh_from_db()
        self.assertEqual(self.gen_res.metadata.subjects.count(), 3)

        # here we are testing the update_metadata_element view function

        # update title metadata
        self.assertEqual(self.gen_res.metadata.title.value,
                         'Resource Key/Value Metadata Testing')
        title_element = self.gen_res.metadata.title

        url_params = {'shortkey': self.gen_res.short_id, 'element_name': 'title',
                      'element_id': title_element.id}
        post_data = {'value': 'Updated Resource Title'}
        url = reverse('update_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.set_request_message_attributes(request)
        response = update_metadata_element(request, shortkey=self.gen_res.short_id,
                                           element_name='title', element_id=title_element.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content.decode())
        self.assertEqual(response_dict['status'], 'success')
        self.gen_res.refresh_from_db()
        self.assertEqual(self.gen_res.metadata.title.value, 'Updated Resource Title')

        # here we are testing the delete_metadata_element view function

        # first create a contributor element and then delete it
        # there should be no contributors now
        self.assertEqual(self.gen_res.metadata.contributors.count(), 0)
        url_params = {'shortkey': self.gen_res.short_id, 'element_name': 'contributor'}
        post_data = {'name': 'John Smith', 'email': 'jm@gmail.com'}
        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.set_request_message_attributes(request)
        response = add_metadata_element(request, shortkey=self.gen_res.short_id,
                                        element_name='contributor')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content.decode())
        self.assertEqual(response_dict['status'], 'success')
        self.assertEqual(response_dict['element_name'], 'contributor')
        self.gen_res.refresh_from_db()
        # there should be one contributor now
        self.assertEqual(self.gen_res.metadata.contributors.count(), 1)

        # now delete the contributor we created above
        contributor = self.gen_res.metadata.contributors.first()
        url_params = {'shortkey': self.gen_res.short_id, 'element_name': 'contributor',
                      'element_id': contributor.id}

        url = reverse('delete_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.user

        request.META['HTTP_REFERER'] = 'some-url'
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = delete_metadata_element(request, shortkey=self.gen_res.short_id,
                                           element_name='contributor', element_id=contributor.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.headers['referer'])
        self.gen_res.refresh_from_db()
        # there should be no contributors
        self.assertEqual(self.gen_res.metadata.contributors.count(), 0)

    @parametrize(
        "resource_type",
        [
            param("CollectionResource", id="collection_resource"),
            param("CompositeResource", id="composite_resource"),
        ],
    )
    @patch('hs_core.views.update_doi_metadata_with_datacite')
    @patch('hs_core.views.resource_modified')
    def test_delete_resource_coverage(self, mock_resource_modified, mock_update_doi_metadata, resource_type):
        test_resource = self.create_resource(resource_type=resource_type)
        # add spatial coverage to the resource
        test_resource.metadata.create_element(
            'coverage',
            type='point',
            value={
                'name': 'Test Point',
                'east': '56.45678',
                'north': '12.6789',
                'units': 'Decimal degrees'
            }
        )
        test_resource.refresh_from_db()
        self.assertIsNotNone(test_resource.metadata.spatial_coverage)

        resource_id = test_resource.short_id
        coverage_type = 'spatial'
        url_params = {'resource_id': resource_id, 'coverage_type': coverage_type}
        url = reverse('delete_resource_coverage', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.user
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = delete_resource_coverage(
            request,
            resource_id=resource_id,
            coverage_type=coverage_type
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content.decode())
        self.assertEqual(response_dict['status'], 'success')
        self.assertEqual(
            response_dict['message'],
            'Resource spatial coverage was deleted successfully.'
        )
        self.assertEqual(response_dict['spatial_coverage'], {})

        test_resource.refresh_from_db()
        self.assertIsNone(test_resource.metadata.spatial_coverage)
        mock_resource_modified.assert_called_once_with(
            test_resource,
            self.user,
            overwrite_bag=False
        )
        mock_update_doi_metadata.assert_called_once_with(
            short_id=resource_id,
            element_name='coverage',
            payload={}
        )

    def test_delete_resource_coverage_invalid_coverage_type(self):
        test_resource = self.create_resource()
        resource_id = test_resource.short_id
        coverage_type = 'invalid'
        url_params = {'resource_id': resource_id, 'coverage_type': coverage_type}
        url = reverse('delete_resource_coverage', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.user
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = delete_resource_coverage(
            request,
            resource_id=resource_id,
            coverage_type=coverage_type
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            json.loads(response.content.decode()),
            {
                'status': 'error',
                'message': f'Invalid coverage type {coverage_type} specified.'
            }
        )

    def test_delete_resource_coverage_invalid_resource_type(self):
        tool_resource = self.create_resource(resource_type='ToolResource')
        resource_id = tool_resource.short_id
        coverage_type = 'temporal'
        url_params = {'resource_id': resource_id, 'coverage_type': coverage_type}
        url = reverse('delete_resource_coverage', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.user
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = delete_resource_coverage(
            request,
            resource_id=resource_id,
            coverage_type=coverage_type
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            json.loads(response.content.decode()),
            {
                'status': 'error',
                'message': 'Coverage can be only be deleted for Composite and Collection type resources.'
            }
        )
