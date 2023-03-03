import json

from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group
from django.urls import reverse

from rest_framework import status

from hs_core import hydroshare
from hs_core.views import unshare_resource_with_user, unshare_resource_with_group
from hs_core.testing import MockIRODSTestCaseMixin
from hs_access_control.models import PrivilegeCodes


class TestUnshareResource(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestUnshareResource, self).setUp()
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

        self.unauthorized_user = hydroshare.create_account(
            'gary@gmail.com',
            username='garyB',
            first_name='Gary',
            last_name='Brandon',
            superuser=False,
            password='gbmypassword',
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

    def test_unshare_resource_with_user(self):
        # here we are testing the unshare_resource_with_user view function

        # test unshare resource with self.user

        # test self.user has no view permission
        self.assertNotIn(self.user, self.gen_res.raccess.view_users)
        # grant view access to self.user
        self.owner.uaccess.share_resource_with_user(self.gen_res, self.user, PrivilegeCodes.VIEW)
        # test self.user has now view permission
        self.gen_res.raccess.refresh_from_db()
        self.assertIn(self.user, self.gen_res.raccess.view_users)

        self._check_unshare_with_user()
        # test self.user has no view permission
        self.assertNotIn(self.user, self.gen_res.raccess.view_users)

        # grant edit access to self.user
        self.owner.uaccess.share_resource_with_user(self.gen_res, self.user, PrivilegeCodes.CHANGE)
        # test self.user has now edit permission
        self.gen_res.raccess.refresh_from_db()
        self.assertIn(self.user, self.gen_res.raccess.edit_users)

        self._check_unshare_with_user()
        # test self.user has no edit permission
        self.assertNotIn(self.user, self.gen_res.raccess.edit_users)

        # grant owner access to self.user
        self.owner.uaccess.share_resource_with_user(self.gen_res, self.user, PrivilegeCodes.OWNER)
        # test self.user has now owner permission
        self.gen_res.raccess.refresh_from_db()
        self.assertIn(self.user, self.gen_res.raccess.owners)

        self._check_unshare_with_user()
        # test self.user has no owner permission
        self.assertNotIn(self.user, self.gen_res.raccess.owners)

        # clean up
        hydroshare.delete_resource(self.gen_res.short_id)

    def test_unshare_resource_with_self(self):
        # here we are testing the unshare_resource_with_user view function

        # test unshare resource with self.user by self.user

        # test self.user has no view permission
        self.assertNotIn(self.user, self.gen_res.raccess.view_users)
        # grant view access to self.user
        self.owner.uaccess.share_resource_with_user(self.gen_res, self.user, PrivilegeCodes.VIEW)
        # test self.user has now view permission
        self.gen_res.raccess.refresh_from_db()
        self.assertIn(self.user, self.gen_res.raccess.view_users)

        url_params = {'shortkey': self.gen_res.short_id, 'user_id': self.user.id}
        url = reverse('unshare_resource_with_user', kwargs=url_params)
        request = self.factory.post(url, data={})
        # self unsharing
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        response = unshare_resource_with_user(request, shortkey=self.gen_res.short_id,
                                              user_id=self.user.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content.decode())
        self.assertEqual(response_data['status'], 'success')
        self.assertEqual(response_data['redirect_to'], '/my-resources/')
        self.gen_res.raccess.refresh_from_db()
        self.assertNotIn(self.user, self.gen_res.raccess.view_users)

    def test_unshare_resource_with_user_bad_request(self):
        # here we are testing the unshare_resource_with_user view function

        # test unshare resource with self.user by unauthorized_user

        # test self.user has no view permission
        self.assertNotIn(self.user, self.gen_res.raccess.view_users)
        # grant view access to self.user
        self.owner.uaccess.share_resource_with_user(self.gen_res, self.user, PrivilegeCodes.VIEW)
        # test self.user has now view permission
        self.gen_res.raccess.refresh_from_db()
        self.assertIn(self.user, self.gen_res.raccess.view_users)

        url_params = {'shortkey': self.gen_res.short_id, 'user_id': self.user.id}
        url = reverse('unshare_resource_with_user', kwargs=url_params)
        request = self.factory.post(url, data={})
        # unauthorized user trying to remove access of self.user
        request.user = self.unauthorized_user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        with self.assertRaises(PermissionDenied):
            unshare_resource_with_user(request, shortkey=self.gen_res.short_id,
                                       user_id=self.user.id)

        self.gen_res.raccess.refresh_from_db()
        self.assertIn(self.user, self.gen_res.raccess.view_users)

    def test_unshare_resource_with_group(self):
        # here we are testing the unshare_resource_with_group view function

        # test unshare resource with self.test_group

        # test self.test_group has no view permission
        self.assertNotIn(self.test_group, self.gen_res.raccess.view_groups)
        # grant view access to self.test_group
        self.owner.uaccess.share_resource_with_group(self.gen_res, self.test_group,
                                                     PrivilegeCodes.VIEW)
        # test self.test_group has now view permission
        self.gen_res.raccess.refresh_from_db()
        self.assertIn(self.test_group, self.gen_res.raccess.view_groups)

        self._check_unshare_with_group()
        # test self.test_group has no view permission
        self.assertNotIn(self.test_group, self.gen_res.raccess.view_groups)

        # grant edit access to test_group
        self.owner.uaccess.share_resource_with_group(self.gen_res, self.test_group,
                                                     PrivilegeCodes.CHANGE)
        # test test_group has now edit permission
        self.gen_res.raccess.refresh_from_db()
        self.assertIn(self.test_group, self.gen_res.raccess.edit_groups)

        self._check_unshare_with_group()
        # test test_group has no edit permission
        self.assertNotIn(self.test_group, self.gen_res.raccess.edit_groups)

        # clean up
        hydroshare.delete_resource(self.gen_res.short_id)

    def test_unshare_resource_with_group_bad_request(self):
        # here we are testing the unshare_resource_with_group view function

        # test unshare resource with test_group by unauthorized_user

        # test test_group has no view permission
        self.assertNotIn(self.test_group, self.gen_res.raccess.view_groups)
        # grant view access to test_group
        self.owner.uaccess.share_resource_with_group(self.gen_res, self.test_group,
                                                     PrivilegeCodes.VIEW)
        # test test_group has now view permission
        self.gen_res.raccess.refresh_from_db()
        self.assertIn(self.test_group, self.gen_res.raccess.view_groups)

        url_params = {'shortkey': self.gen_res.short_id, 'group_id': self.test_group.id}
        url = reverse('unshare_resource_with_group', kwargs=url_params)
        request = self.factory.post(url, data={})
        # unauthorized user trying to remove access of test_group
        request.user = self.unauthorized_user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        with self.assertRaises(PermissionDenied):
            unshare_resource_with_group(request, shortkey=self.gen_res.short_id,
                                        group_id=self.test_group.id)

        self.gen_res.raccess.refresh_from_db()
        self.assertIn(self.test_group, self.gen_res.raccess.view_groups)

    def _check_unshare_with_user(self):

        url_params = {'shortkey': self.gen_res.short_id, 'user_id': self.user.id}
        url = reverse('unshare_resource_with_user', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.owner
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        response = unshare_resource_with_user(request, shortkey=self.gen_res.short_id,
                                              user_id=self.user.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content.decode())
        self.assertEqual(response_data['status'], 'success')
        self.gen_res.raccess.refresh_from_db()

    def _check_unshare_with_group(self):
        url_params = {'shortkey': self.gen_res.short_id, 'group_id': self.test_group.id}
        url = reverse('unshare_resource_with_group', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.owner
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        response = unshare_resource_with_group(request, shortkey=self.gen_res.short_id,
                                               group_id=self.test_group.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content.decode())
        self.assertEqual(response_data['status'], 'success')
        self.gen_res.raccess.refresh_from_db()
