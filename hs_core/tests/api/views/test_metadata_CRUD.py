import os
import shutil
import json

from django.contrib.auth.models import Group
from django.urls import reverse

from rest_framework import status

from hs_core import hydroshare
from hs_core.views import add_metadata_element, update_metadata_element, delete_metadata_element
from hs_core.testing import MockIRODSTestCaseMixin, ViewTestCase


class TestCRUDMetadata(MockIRODSTestCaseMixin, ViewTestCase):
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
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        self.gen_res.refresh_from_db()
        # there should be no contributors
        self.assertEqual(self.gen_res.metadata.contributors.count(), 0)

        hydroshare.delete_resource(self.gen_res.short_id)
