import json

from django.contrib.auth.models import User, Group
from rest_framework import status

from hs_core.hydroshare import resource
from hs_core.tests.api.rest.base import HSRESTTestCase
from hs_access_control.models.privilege import PrivilegeCodes


class TestResourcePermission(HSRESTTestCase):
    def setUp(self):
        super(TestResourcePermission, self).setUp()

        # Create a test resource owned by the default user
        self.res = resource.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Resource for testing Permission',
        )

        # Create test groups
        self.edit_group = self.user.uaccess.create_group(
            title='edit_group',
            description='Group for resource edit permission testing'
        )
        self.view_group = self.user.uaccess.create_group(
            title='view_group',
            description='Group for resource view permission testing'
        )

        # Create users
        self.edit_user = User.objects.create_user(
            username='edituser',
            email='edituser@example.com',
            password='edituser'
        )

        self.view_user = User.objects.create_user(
            username='viewuser',
            email='viewuser@example.com',
            password='viewuser'
        )

        self.no_perm_user = User.objects.create_user(
            username='nopermuser',
            email='nopermuser@example.com',
            password='nopermuser'
        )

        # Create group users
        self.edit_user_via_group = User.objects.create_user(
            username='groupedituser',
            email='groupedituser@example.com',
            password='groupedituser'
        )
        self.view_user_via_group = User.objects.create_user(
            username='groupviewuser',
            email='groupviewuser@example.com',
            password='groupviewuser'
        )

        # Add users to groups using proper access control
        self.user.uaccess.share_group_with_user(
            self.edit_group,
            self.edit_user_via_group,
            PrivilegeCodes.VIEW # edit_user_via_group has view permission on edit_group
        )
        self.user.uaccess.share_group_with_user(
            self.view_group,
            self.view_user_via_group,
            PrivilegeCodes.CHANGE # view_user_via_group has edit permission on view_group
        )

        # Set individual permissions
        self.user.uaccess.share_resource_with_user(
            self.res, self.edit_user, PrivilegeCodes.CHANGE)

        self.user.uaccess.share_resource_with_user(
            self.res, self.view_user, PrivilegeCodes.VIEW)

        # Set group permissions
        self.user.uaccess.share_resource_with_group(
            self.res,
            self.edit_group,
            PrivilegeCodes.CHANGE
        )
        self.user.uaccess.share_resource_with_group(
            self.res,
            self.view_group,
            PrivilegeCodes.VIEW
        )

        # URL for the permission endpoint
        self.url = "/hsapi2/resource/{}/permission/json/".format(self.res.short_id)

    def test_get_permission_owner(self):
        # Test owner permission
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'owner')

    def test_get_permission_edit(self):
        # Test edit permission
        self.client.logout()
        self.client.login(username='edituser', password='edituser')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'edit')

    def test_get_permission_view(self):
        # Test view permission
        self.client.logout()
        self.client.login(username='viewuser', password='viewuser')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'view')

    def test_get_permission_none(self):
        # Test no permission
        self.client.logout()
        self.client.login(username='nopermuser', password='nopermuser')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'none')

    def test_get_permission_nonexistent_resource(self):
        # Test with non-existent resource
        nonexistent_url = "/hsapi2/resource/abc123/permission/json/"
        response = self.client.get(nonexistent_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'none')

    def test_get_permission_anonymous_user(self):
        # Test no permission
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'none')

    def test_get_permission_group_edit(self):
        # Test edit permission through group membership
        self.client.logout()
        self.client.login(username='groupedituser', password='groupedituser')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'edit')

    def test_get_permission_group_view(self):
        # Test view permission through group membership
        self.client.logout()
        self.client.login(username='groupviewuser', password='groupviewuser')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'view')

    def test_get_permission_highest_privilege(self):
        # Test user gets highest privilege when they have both direct and group permissions
        self.user.uaccess.share_group_with_user(
            self.edit_group,
            self.view_user,
            PrivilegeCodes.CHANGE # view_user has edit permission on edit_group
        )

        self.client.logout()
        self.client.login(username='viewuser', password='viewuser')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        # view_user has both edit (via group) and view (direct) permission on the resource
        self.assertEqual(response_json['permission'], 'edit')
