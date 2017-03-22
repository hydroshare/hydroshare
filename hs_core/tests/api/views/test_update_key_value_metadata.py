import json

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.urlresolvers import reverse

from rest_framework import status

from hs_core import hydroshare
from hs_core.views import update_key_value_metadata
from hs_core.testing import MockIRODSTestCaseMixin


class TestUpdateKeyValueMetadata(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestUpdateKeyValueMetadata, self).setUp()
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
            resource_type='GenericResource',
            owner=self.user,
            title='Generic Resource Key/Value Metadata Testing'
        )

        self.factory = RequestFactory()

    def test_update_key_value_metadata(self):
        # here we are testing the update_key_value_metadata view function

        # no key/value metadata at this point
        self.assertEqual(self.gen_res.extra_metadata, {})

        # create key/value metadata
        url_params = {'shortkey': self.gen_res.short_id}
        post_data = {'key1': 'key-1', 'value1': 'value-1'}
        url = reverse('update_key_value_metadata', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self._set_request_message_attributes(request)
        response = update_key_value_metadata(request, shortkey=self.gen_res.short_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual(response_dict['status'], 'success')
        self.gen_res.refresh_from_db()
        self.assertEqual(self.gen_res.extra_metadata, post_data)

        # update key/value metadata
        url_params = {'shortkey': self.gen_res.short_id}
        post_data = {'key1A': 'key-1A', 'value1': 'value-1',
                     'key1B': 'key-1B', 'value1B': 'value-1B'}
        url = reverse('update_key_value_metadata', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self._set_request_message_attributes(request)
        response = update_key_value_metadata(request, shortkey=self.gen_res.short_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content)
        self.assertEqual(response_dict['status'], 'success')
        self.gen_res.refresh_from_db()
        self.assertEqual(self.gen_res.extra_metadata, post_data)

        hydroshare.delete_resource(self.gen_res.short_id)

    def _set_request_message_attributes(self, request):
        # the following 3 lines are for preventing error in unit test due to the view being
        # tested uses messaging middleware
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
