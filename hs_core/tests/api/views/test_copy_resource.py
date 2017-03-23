from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse

from rest_framework import status

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.views import copy_resource
from hs_core.testing import MockIRODSTestCaseMixin


class TestCopyResource(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestCopyResource, self).setUp()
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

    def test_copy_resource(self):
        # here we are testing the copy_resource view function

        # we should have 1 resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(BaseResource.objects.count(), 1)
        url_params = {'shortkey': self.gen_res.short_id}
        url = reverse('copy_resource', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.user

        self._add_session_to_request(request)
        response = copy_resource(request, shortkey=self.gen_res.short_id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        res_id = response.url.split('/')[2]
        self.assertEqual(BaseResource.objects.filter(short_id=res_id).exists(), True)
        # should have 2 resources now
        self.assertEqual(BaseResource.objects.count(), 2)

        # clean up
        hydroshare.delete_resource(res_id)
        hydroshare.delete_resource(self.gen_res.short_id)

    def _add_session_to_request(self, request):
        """Annotate a request object with a session"""
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()