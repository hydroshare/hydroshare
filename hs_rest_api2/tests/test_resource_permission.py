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

        # Create additional users with different permission levels
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

        # Set permissions for users
        self.user.uaccess.share_resource_with_user(
            self.res, self.edit_user, PrivilegeCodes.CHANGE)

        self.user.uaccess.share_resource_with_user(
            self.res, self.view_user, PrivilegeCodes.VIEW)

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
