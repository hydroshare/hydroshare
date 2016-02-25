from django.test import TestCase
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin
from hs_access_control.models import PrivilegeCodes

class TestCreateResourceVersion(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestCreateResourceVersion, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='administrator',
            last_name='dash',
            superuser=True,
            groups=[]
        )

        self.owner = hydroshare.create_account(
            'owner@gmail.com',
            username='owner',
            first_name='owner',
            last_name='dash',
            superuser=False,
            groups=[]
        )
        self.editor = hydroshare.create_account(
            'editor@gmail.com',
            username='editor',
            first_name='editor',
            last_name='dash',
            superuser=False,
            groups=[]
        )
        self.viewer = hydroshare.create_account(
            'viewer@gmail.com',
            username='viewer',
            first_name='viewer',
            last_name='dash',
            superuser=False,
            groups=[]
        )

        self.user = hydroshare.create_account(
            'user@gmail.com',
            username='user',
            first_name='user',
            last_name='dash',
            superuser=False,
            groups=[]
        )

        self.resource = hydroshare.create_resource(resource_type='GenericResource',
                                                   owner=self.owner,
                                                   title='Generic Test Resource'
                                                  )

    def test_create_version(self):
        # superuser/admin should be able to create a resource version
        self.assertTrue(self.admin.uaccess.can_create_resource_version(self.resource))

        # owner should be able to create a resource version
        self.assertTrue(self.owner.uaccess.can_create_resource_version(self.resource))

        # grant editor edit permission
        self.owner.uaccess.share_resource_with_user(self.resource, self.editor, PrivilegeCodes.CHANGE)
        # resource editor can't create resource version
        self.assertFalse(self.editor.uaccess.can_create_resource_version(self.resource))

        # grant viewer view permission
        self.owner.uaccess.share_resource_with_user(self.resource, self.viewer, PrivilegeCodes.VIEW)
        # resource viewer can't create resource version
        self.assertFalse(self.viewer.uaccess.can_create_resource_version(self.resource))

        # authenticated user with no granted privilege can't create resource version
        self.assertFalse(self.user.uaccess.can_create_resource_version(self.resource))

    def test_create_version_inactive_user(self):
        # inactive superuser/admin should not be able to create a resource version
        self.admin.is_active = False
        self.admin.save()
        with self.assertRaises(PermissionDenied):
            self.admin.uaccess.can_create_resource_version(self.resource)

        # inactive resource owner should not be able to create a resource version
        self.owner.is_active = False
        self.owner.save()
        with self.assertRaises(PermissionDenied):
            self.owner.uaccess.can_create_resource_version(self.resource)

        self.owner.is_active = True
        self.owner.save()

        # grant editor edit permission
        self.owner.uaccess.share_resource_with_user(self.resource, self.editor, PrivilegeCodes.CHANGE)
        # inactive editor should not be able to create a resource version
        self.editor.is_active = False
        self.editor.save()
        with self.assertRaises(PermissionDenied):
            self.editor.uaccess.can_create_resource_version(self.resource)

        # grant viewer view permission
        self.owner.uaccess.share_resource_with_user(self.resource, self.viewer, PrivilegeCodes.VIEW)
        # inactive viewer should not be able to create a resource version
        self.viewer.is_active = False
        self.viewer.save()
        with self.assertRaises(PermissionDenied):
            self.viewer.uaccess.can_create_resource_version(self.resource)

        # inactive user should not be able to create a resource version
        self.user.is_active = False
        self.user.save()
        with self.assertRaises(PermissionDenied):
            self.user.uaccess.can_create_resource_version(self.resource)