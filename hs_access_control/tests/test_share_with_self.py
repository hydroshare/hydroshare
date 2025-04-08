
from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group

from hs_access_control.models import PrivilegeCodes

from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin

from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set


class T05ShareResource(MockS3TestCaseMixin, TestCase):

    def setUp(self):
        super(T05ShareResource, self).setUp()
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

        # use this as non owner
        self.mouse = hydroshare.create_account(
            'mouse@gmail.com',
            username='mouse',
            first_name='first_name_mouse',
            last_name='last_name_mouse',
            superuser=False,
            groups=[]
        )
        self.holes = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.cat,
            title='all about dog holes',
            metadata=[],
        )

        self.meowers = self.cat.uaccess.create_group(
            title='some random meowers', description="some random group")

    def test_01_self_unshare_resource(self):
        """A user can unshare a resource with self"""
        holes = self.holes
        cat = self.cat
        dog = self.dog
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(dog in holes.raccess.edit_users)
        self.assertTrue(dog in holes.raccess.view_users)
        self.assertTrue(
            is_equal_to_as_set(
                [dog],
                dog.uaccess.get_resource_unshare_users(holes)))
        dog.uaccess.unshare_resource_with_user(holes, dog)
        self.assertFalse(dog in holes.raccess.edit_users)
        self.assertFalse(dog in holes.raccess.view_users)
        self.assertTrue(
            is_equal_to_as_set(
                [], dog.uaccess.get_resource_unshare_users(holes)))

    def test_02_self_downgrade_resource(self):
        """can downgrade privilege for a resource to which one has access"""
        holes = self.holes
        cat = self.cat
        dog = self.dog
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(dog in holes.raccess.edit_users)
        self.assertTrue(dog in holes.raccess.view_users)
        self.assertTrue(
            is_equal_to_as_set(
                [dog],
                dog.uaccess.get_resource_unshare_users(holes)))
        dog.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)
        self.assertFalse(dog in holes.raccess.edit_users)
        self.assertTrue(dog in holes.raccess.view_users)
        self.assertTrue(
            is_equal_to_as_set(
                [dog],
                dog.uaccess.get_resource_unshare_users(holes)))

    def test_03_self_cannot_upgrade_resource(self):
        """cannot upgrade privilege for a resource to which one has access"""
        holes = self.holes
        cat = self.cat
        dog = self.dog
        cat.uaccess.share_resource_with_user(holes, dog, PrivilegeCodes.VIEW)
        self.assertFalse(dog in holes.raccess.edit_users)
        self.assertTrue(dog in holes.raccess.view_users)
        self.assertTrue(
            is_equal_to_as_set(
                [dog],
                dog.uaccess.get_resource_unshare_users(holes)))
        with self.assertRaises(PermissionDenied):
            dog.uaccess.share_resource_with_user(
                holes, dog, PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied):
            dog.uaccess.share_resource_with_user(
                holes, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(dog in holes.raccess.view_users)
        self.assertTrue(
            is_equal_to_as_set(
                [dog],
                dog.uaccess.get_resource_unshare_users(holes)))

    def test_04_self_unshare_group(self):
        """A user can unshare a group with self"""
        meowers = self.meowers
        cat = self.cat
        dog = self.dog
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(dog in meowers.gaccess.edit_users)
        self.assertTrue(dog in meowers.gaccess.members)
        self.assertTrue(
            is_equal_to_as_set(
                [dog],
                dog.uaccess.get_group_unshare_users(meowers)))
        dog.uaccess.unshare_group_with_user(meowers, dog)
        self.assertFalse(dog in meowers.gaccess.edit_users)
        self.assertFalse(dog in meowers.gaccess.members)
        self.assertTrue(
            is_equal_to_as_set(
                [], dog.uaccess.get_group_unshare_users(meowers)))

    def test_05_self_can_downgrade_group(self):
        """can downgrade privilege for a group of which one is a member """
        meowers = self.meowers
        cat = self.cat
        dog = self.dog
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(dog in meowers.gaccess.edit_users)
        self.assertTrue(dog in meowers.gaccess.members)
        self.assertTrue(
            is_equal_to_as_set(
                [dog],
                dog.uaccess.get_group_unshare_users(meowers)))
        dog.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.VIEW)
        self.assertFalse(dog in meowers.gaccess.edit_users)
        self.assertTrue(dog in meowers.gaccess.members)
        self.assertTrue(
            is_equal_to_as_set(
                [dog],
                dog.uaccess.get_group_unshare_users(meowers)))

    def test_06_self_cannot_upgrade_group(self):
        """cannot upgrade privilege for a group of which one is a member """
        meowers = self.meowers
        cat = self.cat
        dog = self.dog
        cat.uaccess.share_group_with_user(meowers, dog, PrivilegeCodes.VIEW)
        self.assertFalse(dog in meowers.gaccess.edit_users)
        self.assertTrue(dog in meowers.gaccess.members)
        self.assertTrue(
            is_equal_to_as_set(
                [dog],
                dog.uaccess.get_group_unshare_users(meowers)))
        with self.assertRaises(PermissionDenied):
            dog.uaccess.share_group_with_user(
                meowers, dog, PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied):
            dog.uaccess.share_group_with_user(
                meowers, dog, PrivilegeCodes.CHANGE)
        self.assertTrue(dog in meowers.gaccess.members)
        self.assertTrue(
            is_equal_to_as_set(
                [dog],
                dog.uaccess.get_group_unshare_users(meowers)))
