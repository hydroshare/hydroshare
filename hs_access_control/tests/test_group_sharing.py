from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group

from hs_access_control.models import GroupResourcePrivilege, UserGroupPrivilege, PrivilegeCodes

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set, \
    assertGroupResourceUnshareCoherence


class T09GroupSharing(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(T09GroupSharing, self).setUp()
        global_reset()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='administrator',
            last_name='couch',
            superuser=True,
            groups=[]
        )

        self.cat = hydroshare.create_account(
            'cat@gmail.com',
            username='cat',
            first_name='not a dog',
            last_name='last_name_cat',
            superuser=False,
            groups=[]
        )

        self.dog = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            first_name='a little arfer',
            last_name='last_name_dog',
            superuser=False,
            groups=[]
        )

        self.bat = hydroshare.create_account(
            'bat@gmail.com',
            username='bat',
            first_name='not a man',
            last_name='last_name_bat',
            superuser=False,
            groups=[]
        )

        self.nobody = hydroshare.create_account(
            'nobody@gmail.com',
            username='nobody',
            first_name='no one in particular',
            last_name='last_name_nobody',
            superuser=False,
            groups=[]
        )

        self.scratching = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.dog,
            title='all about sofas as scrathing posts',
            metadata=[],
        )

        # dog owns felines group
        self.felines = self.dog.uaccess.create_group(
            title='felines', description="We are the felines")
        self.dog.uaccess.share_group_with_user(
            self.felines, self.cat, PrivilegeCodes.VIEW)  # poetic justice

    def test_00_defaults(self):
        """Defaults are correct when creating groups"""
        scratching = self.scratching
        felines = self.felines
        dog = self.dog

        # TODO: check for group existence via uuid handle

        self.assertTrue(felines.gaccess.discoverable)
        self.assertTrue(felines.gaccess.public)
        self.assertTrue(felines.gaccess.shareable)

        self.assertTrue(dog.uaccess.owns_group(felines))
        self.assertTrue(dog.uaccess.can_change_group(felines))
        self.assertTrue(dog.uaccess.can_view_group(felines))

        self.assertTrue(dog.uaccess.can_view_resource(scratching))
        self.assertTrue(dog.uaccess.can_change_resource(scratching))
        self.assertTrue(dog.uaccess.owns_resource(scratching))

        assertGroupResourceUnshareCoherence(self)

    def test_01_cannot_share_own(self):
        """Groups cannot 'own' resources"""
        scratching = self.scratching
        felines = self.felines
        dog = self.dog
        self.assertFalse(
            dog.uaccess.can_share_resource_with_group(
                scratching, felines, PrivilegeCodes.OWNER))
        with self.assertRaises(PermissionDenied) as cm:
            dog.uaccess.share_resource_with_group(
                scratching, felines, PrivilegeCodes.OWNER)
        self.assertEqual(str(cm.exception), 'Groups cannot own resources')

        assertGroupResourceUnshareCoherence(self)

    def test_02_share_rw(self):
        """An owner can share with CHANGE privileges"""
        scratching = self.scratching
        felines = self.felines
        dog = self.dog
        cat = self.cat
        nobody = self.nobody

        self.assertTrue(
            dog.uaccess.can_share_resource_with_group(
                scratching,
                felines,
                PrivilegeCodes.CHANGE))
        dog.uaccess.share_resource_with_group(
            scratching, felines, PrivilegeCodes.CHANGE)

        # is the resource just shared with this group?
        self.assertEqual(felines.gaccess.view_resources.count(), 1)
        self.assertTrue(
            is_equal_to_as_set(
                [scratching],
                felines.gaccess.view_resources))

        # check that flags haven't changed
        self.assertTrue(felines.gaccess.discoverable)
        self.assertTrue(felines.gaccess.public)
        self.assertTrue(cat.uaccess.can_view_group(felines))
        self.assertFalse(cat.uaccess.can_change_group(felines))
        self.assertFalse(cat.uaccess.owns_group(felines))

        self.assertFalse(cat.uaccess.owns_resource(scratching))
        self.assertTrue(cat.uaccess.can_change_resource(scratching))
        self.assertTrue(cat.uaccess.can_view_resource(scratching))

        # should be able to unshare anything one shared.
        with self.assertRaises(PermissionDenied) as cm:
            nobody.uaccess.unshare_resource_with_group(scratching, felines)
        self.assertEqual(str(cm.exception),
                         'Insufficient privilege to unshare resource')

        assertGroupResourceUnshareCoherence(self)

        self.assertTrue(
            dog.uaccess.can_unshare_resource_with_group(
                scratching, felines))
        dog.uaccess.unshare_resource_with_group(scratching, felines)
        self.assertEqual(felines.gaccess.view_resources.count(), 0)

        assertGroupResourceUnshareCoherence(self)

    def test_03_group_share_printing(self):
        """ test group share record printing """
        dog = self.dog
        scratching = self.scratching
        felines = self.felines
        self.assertTrue(
            dog.uaccess.can_share_resource_with_group(
                scratching,
                felines,
                PrivilegeCodes.CHANGE))
        dog.uaccess.share_resource_with_group(
            scratching, felines, PrivilegeCodes.CHANGE)

        text = str(
            GroupResourcePrivilege.objects.get(
                resource=scratching,
                group=felines))
        self.assertTrue(text.find(felines.name) >= 0)

        text = str(UserGroupPrivilege.objects.get(user=dog, group=felines))
        self.assertTrue(text.find(felines.name) >= 0)
