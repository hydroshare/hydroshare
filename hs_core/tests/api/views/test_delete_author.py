import os
import shutil
import json

from django.contrib.auth.models import Group, User
from django.urls import reverse

from rest_framework import status

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.views import add_metadata_element, delete_author
from hs_core.testing import MockS3TestCaseMixin, ViewTestCase


class TestDeleteAuthor(MockS3TestCaseMixin, ViewTestCase):
    def setUp(self):
        super(TestDeleteAuthor, self).setUp()
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
            title='My Test Resource'
        )

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        super(TestDeleteAuthor, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()

    def test_delete_author(self):
        # testing the delete_author view function
        # add an author element and then delete it

        # the resource should have only the original author now
        self.assertEqual(self.gen_res.metadata.creators.count(), 1)
        url_params = {'shortkey': self.gen_res.short_id, 'element_name': 'creator'}
        post_data = {'name': 'Smith, John', 'email': 'jm@gmail.com'}
        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        # make it an ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.set_request_message_attributes(request)
        response = add_metadata_element(request, shortkey=self.gen_res.short_id,
                                        element_name='creator')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content.decode())
        self.assertEqual(response_dict['status'], 'success')
        self.assertEqual(response_dict['element_name'], 'creator')
        self.gen_res.refresh_from_db()
        # there should be two authors now
        self.assertEqual(self.gen_res.metadata.creators.count(), 2)

        # delete the author we added above
        author = self.gen_res.metadata.creators.all()[1]
        url_params = {'shortkey': self.gen_res.short_id, 'element_id': author.id}

        url = reverse('delete_author', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.user

        request.META['HTTP_REFERER'] = 'some-url'
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = delete_author(request, shortkey=self.gen_res.short_id, element_id=author.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.gen_res.refresh_from_db()
        # there should be only the original author now
        self.assertEqual(self.gen_res.metadata.creators.count(), 1)

        hydroshare.delete_resource(self.gen_res.short_id)
