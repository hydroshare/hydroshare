import json

from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group
from django.urls import reverse

from rest_framework import status

from hs_core import hydroshare
from hs_core.views import share_resource_with_user, share_resource_with_group
from hs_core.testing import MockIRODSTestCaseMixin


class TestShareResource(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestShareResource, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        self.owner = hydroshare.create_account(
            'john@gmail.com',
            username='john',
            first_name='John',
            last_name='Clarson',
            superuser=False,
            password='jhmypassword',
            groups=[]
        )

        self.user = hydroshare.create_account(
            'lisa@gmail.com',
            username='lisaZ',
            first_name='Lisa',
            last_name='Ziggler',
            superuser=False,
            password='lzmypassword',
            groups=[]
        )
        # crate a group for testing group access to resource
        self.test_group = self.owner.uaccess.create_group(
            title='Test Group',
            description="This is to test group access to resource",
            purpose="Testing group access to resource")

        self.gen_res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.owner,
            title='Resource Share Resource Testing'
        )

        self.factory = RequestFactory()

    def test_share_resource_with_user(self):
        # here we are testing the share_resource_with_user view function

        # test share resource with self.user with view permission

        # test self.user has no view permission
        self.assertNotIn(self.user, self.gen_res.raccess.view_users)
        self._check_share_with_user(privilege='view')
        # test self.user has now view permission
        self.assertIn(self.user, self.gen_res.raccess.view_users)

        # test share resource with self.user with edit permission

        # test self.user has no edit permission
        self.assertNotIn(self.user, self.gen_res.raccess.edit_users)
        self._check_share_with_user(privilege='edit')
        # test self.user has now edit permission
        self.assertIn(self.user, self.gen_res.raccess.edit_users)

        # test share resource with self.user with owner permission

        # test self.user has no owner permission
        self.assertNotIn(self.user, self.gen_res.raccess.owners)
        self._check_share_with_user(privilege='owner')
        # test self.user has now owner permission
        self.assertIn(self.user, self.gen_res.raccess.owners)

        # clean up
        hydroshare.delete_resource(self.gen_res.short_id)

    def test_share_resource_with_user_bad_requests(self):
        # here we are testing the share_resource_with_user view function with bad requests
        bad_privilege = 'bad'
        url_params = {'shortkey': self.gen_res.short_id, 'privilege': bad_privilege,
                      'user_id': self.user.id}
        url = reverse('share_resource_with_user', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.owner
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        response = share_resource_with_user(request, shortkey=self.gen_res.short_id,
                                            privilege=bad_privilege, user_id=self.user.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = json.loads(response.content.decode())
        self.assertEqual(response_data['status'], 'error')

        url_params = {'shortkey': self.gen_res.short_id, 'privilege': 'view',
                      'user_id': self.user.id}
        url = reverse('share_resource_with_user', kwargs=url_params)
        request = self.factory.post(url, data={})
        # user does not have permission to grant himself access to resource
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        with self.assertRaises(PermissionDenied):
            share_resource_with_user(request, shortkey=self.gen_res.short_id,
                                     privilege='view', user_id=self.user.id)
        # clean up
        hydroshare.delete_resource(self.gen_res.short_id)

    def test_share_resource_with_group(self):
        # here we are testing the share_resource_with_group view function

        # test share resource with self.test_group with view permission

        # test self.test_group has no view permission
        self.assertNotIn(self.test_group, self.gen_res.raccess.view_groups)
        self._check_share_with_group(privilege='view')
        self.gen_res.raccess.refresh_from_db()
        # test self.test_group has now view permission
        self.assertIn(self.test_group, self.gen_res.raccess.view_groups)

        # test share resource with self.test_group with edit permission

        # test self.test_group has no edit permission
        self.assertNotIn(self.test_group, self.gen_res.raccess.edit_groups)
        self._check_share_with_group(privilege='edit')
        self.gen_res.raccess.refresh_from_db()
        # test self.test_group has now edit permission
        self.assertIn(self.test_group, self.gen_res.raccess.edit_groups)
        # clean up
        hydroshare.delete_resource(self.gen_res.short_id)

    def test_share_resource_with_group_bad_requests(self):
        # here we are testing the share_resource_with_group view function with bad requests
        bad_privilege = 'bad'
        url_params = {'shortkey': self.gen_res.short_id, 'privilege': bad_privilege,
                      'group_id': self.test_group.id}
        url = reverse('share_resource_with_group', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.owner
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        response = share_resource_with_group(request, shortkey=self.gen_res.short_id,
                                             privilege=bad_privilege, group_id=self.test_group.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = json.loads(response.content.decode())
        self.assertEqual(response_data['status'], 'error')

        # test group can't be given ownership access
        url_params = {'shortkey': self.gen_res.short_id, 'privilege': 'owner',
                      'group_id': self.test_group.id}
        url = reverse('share_resource_with_group', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.owner
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        response = share_resource_with_group(request, shortkey=self.gen_res.short_id,
                                             privilege='owner', group_id=self.test_group.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = json.loads(response.content.decode())
        self.assertEqual(response_data['status'], 'error')

        url_params = {'shortkey': self.gen_res.short_id, 'privilege': 'view',
                      'group_id': self.test_group.id}
        url = reverse('share_resource_with_group', kwargs=url_params)
        request = self.factory.post(url, data={})
        # user does not have permission to grant test_group access to resource
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        with self.assertRaises(PermissionDenied):
            share_resource_with_group(request, shortkey=self.gen_res.short_id,
                                      privilege='view', group_id=self.test_group.id)
        # clean up
        hydroshare.delete_resource(self.gen_res.short_id)

    def _check_share_with_user(self, privilege):

        url_params = {'shortkey': self.gen_res.short_id, 'privilege': privilege,
                      'user_id': self.user.id}
        url = reverse('share_resource_with_user', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.owner
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        response = share_resource_with_user(request, shortkey=self.gen_res.short_id,
                                            privilege=privilege, user_id=self.user.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content.decode())
        self.assertEqual(response_data['status'], 'success')
        self.gen_res.raccess.refresh_from_db()

    def _check_share_with_group(self, privilege):

        url_params = {'shortkey': self.gen_res.short_id, 'privilege': privilege,
                      'group_id': self.test_group.id}
        url = reverse('share_resource_with_group', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.owner
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        response = share_resource_with_group(request, shortkey=self.gen_res.short_id,
                                             privilege=privilege, group_id=self.test_group.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content.decode())
        self.assertEqual(response_data['status'], 'success')
        self.gen_res.raccess.refresh_from_db()
