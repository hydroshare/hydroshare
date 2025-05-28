import json

from django.contrib.auth.models import User
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
        # a group that will have edit permission on the resource
        self.res_edit_group = self.user.uaccess.create_group(
            title='res_edit_group',
            description='Group for resource edit permission testing'
        )
        # a group that will have view permission on the resource
        self.res_view_group = self.user.uaccess.create_group(
            title='res_view_group',
            description='Group for resource view permission testing'
        )

        # Create users
        # a user that will have edit permission on the resource
        self.res_edit_user = User.objects.create_user(
            username='res-edit-user',
            email='res-edit-user@example.com',
            password='res-edit-user'
        )

        # a user that will have view permission on the resource
        self.res_view_user = User.objects.create_user(
            username='res-view-user',
            email='res-view-user@example.com',
            password='res-view-user'
        )

        # a user that will have either view or edit permission on the resource
        self.res_view_or_edit_user = User.objects.create_user(
            username='res-view-or-edit-user',
            email='res-view-or-edit-user@example.com',
            password='res-view-or-edit-user'
        )

        # a user that will have no permission on the resource
        self.no_perm_user = User.objects.create_user(
            username='nopermuser',
            email='nopermuser@example.com',
            password='nopermuser'
        )

        # Create group users
        # a user that will have edit permission on the resource via group membership
        self.res_edit_user_via_group = User.objects.create_user(
            username='res-edit-user-via-group',
            email='res-edit-user-via-group@example.com',
            password='res-edit-user-via-group'
        )
        # a user that will have view permission on the resource via group membership
        self.res_view_user_via_group = User.objects.create_user(
            username='res-view-user-via-group',
            email='res-view-user-via-group@example.com',
            password='res-view-user-via-group'
        )

        # Add users to groups using proper access control
        # user res_edit_user_via_group has view permission (PrivilegeCodes.VIEW) on res_edit_group (won't be
        # able to edit group membership)
        self.user.uaccess.share_group_with_user(
            self.res_edit_group,
            self.res_edit_user_via_group,
            PrivilegeCodes.VIEW
        )

        # user res_view_user_via_group has edit permission (PrivilegeCodes.CHANGE) on res_view_group (will be
        # able to edit group membership)
        self.user.uaccess.share_group_with_user(
            self.res_view_group,
            self.res_view_user_via_group,
            PrivilegeCodes.CHANGE
        )

        # Set individual permissions on the resource
        # grant res_edit_user edit permission on the resource
        self.user.uaccess.share_resource_with_user(
            self.res, self.res_edit_user, PrivilegeCodes.CHANGE)

        # grant res_view_user view permission on the resource
        self.user.uaccess.share_resource_with_user(
            self.res, self.res_view_user, PrivilegeCodes.VIEW)

        # Set group permissions on the resource
        # grant res_edit_group edit permission on the resource - members of res_edit_group have edit
        # permission on the resource
        self.user.uaccess.share_resource_with_group(
            self.res,
            self.res_edit_group,
            PrivilegeCodes.CHANGE
        )

        # grant res_view_group view permission on the resource - members of res_view_group have view
        # permission on the resource
        self.user.uaccess.share_resource_with_group(
            self.res,
            self.res_view_group,
            PrivilegeCodes.VIEW
        )

        # URL for the permission endpoint
        self.url = "/hsapi2/resource/{}/permission/json/".format(self.res.short_id)

    def test_get_permission_owner(self):
        # Test owner permission on the resource
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'owner')

    def test_get_permission_edit(self):
        # Test edit permission on the resource
        self.client.logout()
        self.client.login(username='res-edit-user', password='res-edit-user')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'edit')

    def test_get_permission_view(self):
        # Test view permission on the resource
        self.client.logout()
        self.client.login(username='res-view-user', password='res-view-user')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'view')

    def test_get_permission_none(self):
        # Test no permission on the resource
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
        # Test no permission on the resource
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'none')

    def test_get_permission_group_edit(self):
        # Test edit permission on the resource through group membership
        self.client.logout()
        self.client.login(username='res-edit-user-via-group', password='res-edit-user-via-group')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'edit')

    def test_get_permission_group_view(self):
        # Test view permission on the resource through group membership
        self.client.logout()
        self.client.login(username='res-view-user-via-group', password='res-view-user-via-group')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'view')

    def test_get_permission_highest_privilege(self):
        # Test user gets highest privilege when they have both direct and group permissions

        # grant res_view_or_edit_user view permission on the resource
        self.user.uaccess.share_resource_with_user(
            self.res, self.res_view_or_edit_user, PrivilegeCodes.VIEW)

        # test res_view_or_edit_user has view permission on the resource
        self.client.logout()
        self.client.login(username='res-view-or-edit-user', password='res-view-or-edit-user')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'view')

        # make res_view_or_edit_user a member of res_edit_group - with membership edit permission
        self.user.uaccess.share_group_with_user(
            self.res_edit_group,
            self.res_view_or_edit_user,
            PrivilegeCodes.CHANGE
        )

        # test res_view_or_edit_user has edit permission on the resource via group membership
        self.client.logout()
        self.client.login(username='res-view-or-edit-user', password='res-view-or-edit-user')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['permission'], 'edit')
