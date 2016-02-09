__author__ = 'Alva'

import unittest
from django.http import Http404
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group
from pprint import pprint

from hs_access_control.models import UserAccess, GroupAccess, ResourceAccess, \
    UserResourcePrivilege, GroupResourcePrivilege, UserGroupPrivilege, PrivilegeCodes

from hs_core import hydroshare
from hs_core.models import GenericResource, BaseResource
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.tests.utilities import *


class T08ResourceFlags(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(T08ResourceFlags, self).setUp()
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

        self.bones = hydroshare.create_resource(resource_type='GenericResource',
                                                owner=self.dog,
                                                title='all about dog bones',
                                                metadata=[],)

        self.chewies = hydroshare.create_resource(resource_type='GenericResource',
                                                  owner=self.dog,
                                                  title='all about dog chewies',
                                                  metadata=[],)

    def test_01_default_flags(self):
        "Flag defaults are correct when resource is created"
        bones = self.bones

        # are resources created with correct defaults?
        self.assertFalse(bones.raccess.immutable)
        self.assertFalse(bones.raccess.public)
        self.assertFalse(bones.raccess.published)
        self.assertFalse(bones.raccess.discoverable)
        self.assertTrue(bones.raccess.shareable)

    def test_02_shareable(self):
        "Resource shareable flag enables resource sharing"
        cat = self.cat
        bones = self.bones
        dog = self.dog

        # make bones not shareable
        bones.raccess.shareable = False
        bones.raccess.save()

        # are resource flags correct?
        self.assertFalse(bones.raccess.immutable)
        self.assertFalse(bones.raccess.public)
        self.assertFalse(bones.raccess.published)
        self.assertFalse(bones.raccess.discoverable)
        self.assertFalse(bones.raccess.shareable)

        # dog is an owner, should be able to share even if shareable is False
        dog.uaccess.share_resource_with_user(bones, cat, PrivilegeCodes.VIEW)

        # should get some privilege, but not an owner of bones
        self.assertFalse(cat.uaccess.owns_resource(bones))
        self.assertFalse(cat.uaccess.can_change_resource(bones))
        self.assertTrue(cat.uaccess.can_view_resource(bones))

        # django admin should be able share even if shareable is False
        self.admin.uaccess.share_resource_with_user(bones, cat, PrivilegeCodes.CHANGE)

    def test_03_not_shareable(self):
        "Resource that is not shareable cannot be shared by non-owner"
        cat = self.cat
        dog = self.dog
        bones = self.bones
        bat = self.bat
        bones.raccess.shareable = False
        bones.raccess.save()

        dog.uaccess.share_resource_with_user(bones, cat, PrivilegeCodes.VIEW)

        # cat should not be able to reshare
        with self.assertRaises(PermissionDenied) as cm:
            cat.uaccess.share_resource_with_user(bones, bat, PrivilegeCodes.VIEW)
        self.assertEqual(cm.exception.message, 'User must own resource or have sharing privilege')

        # django admin still can share
        self.admin.uaccess.share_resource_with_user(bones, bat, PrivilegeCodes.VIEW)

    def test_04_transitive_sharing(self):
        """Resource shared with one user can be shared with another"""
        cat = self.cat
        dog = self.dog
        bones = self.bones
        bat = self.bat

        self.assertFalse(bones.raccess.immutable)
        self.assertFalse(bones.raccess.public)
        self.assertFalse(bones.raccess.published)
        self.assertFalse(bones.raccess.discoverable)
        self.assertTrue(bones.raccess.shareable)

        # first share
        dog.uaccess.share_resource_with_user(bones, cat, PrivilegeCodes.VIEW)
        self.assertFalse(cat.uaccess.owns_resource(bones))
        self.assertFalse(cat.uaccess.can_change_resource(bones))
        self.assertTrue(cat.uaccess.can_view_resource(bones))

        # now cat should be able to share with bat
        cat.uaccess.share_resource_with_user(bones, bat, PrivilegeCodes.VIEW)
        self.assertFalse(bat.uaccess.owns_resource(bones))
        self.assertFalse(bat.uaccess.can_change_resource(bones))
        self.assertTrue(bat.uaccess.can_view_resource(bones))

    def test_05_discoverable(self):
        """Resource can be made discoverable"""
        bones = self.bones

        # can I change discoverable?
        bones.raccess.discoverable = True
        bones.raccess.save()

        self.assertFalse(bones.raccess.immutable)
        self.assertFalse(bones.raccess.public)
        self.assertFalse(bones.raccess.published)
        self.assertTrue(bones.raccess.discoverable)
        self.assertTrue(bones.raccess.shareable)

        self.assertTrue(is_equal_to_as_set([bones], GenericResource.discoverable_resources.all()))

    def test_06_not_discoverable(self):
        """Resource can be made not discoverable and not public"""
        bones = self.bones

        bones.raccess.discoverable = False
        bones.raccess.public = False
        bones.raccess.save()

        self.assertFalse(bones.raccess.immutable)
        self.assertFalse(bones.raccess.public)
        self.assertFalse(bones.raccess.published)
        self.assertFalse(bones.raccess.discoverable)
        self.assertTrue(bones.raccess.shareable)

        names = GenericResource.discoverable_resources.all()
        self.assertEqual(names.count(), 0)

    def test_07_immutable(self):
        """An immutable resource cannot be changed"""
        bones = self.bones
        dog = self.dog
        nobody = self.nobody

        bones.raccess.immutable = True
        bones.raccess.save()

        self.assertTrue(bones.raccess.immutable)
        self.assertFalse(bones.raccess.public)
        self.assertFalse(bones.raccess.published)
        self.assertFalse(bones.raccess.discoverable)
        self.assertTrue(bones.raccess.shareable)

        # ownership should survive downgrading to immutable; otherwise one cuts out ownership privilege completely
        self.assertTrue(dog.uaccess.owns_resource(bones))
        self.assertFalse(dog.uaccess.can_change_resource(bones))
        self.assertTrue(dog.uaccess.can_view_resource(bones))

        # even django admin should not be able to change an immutable resource
        self.assertFalse(self.admin.uaccess.can_change_resource(bones))
        self.assertTrue(self.admin.uaccess.can_view_resource(bones))

        # another user shouldn't be able to read it unless it's also public
        self.assertFalse(nobody.uaccess.owns_resource(bones))
        self.assertFalse(nobody.uaccess.can_change_resource(bones))
        self.assertFalse(nobody.uaccess.can_view_resource(bones))

        # undo immutable
        bones.raccess.immutable = False
        bones.raccess.save()

        self.assertFalse(bones.raccess.immutable)
        self.assertFalse(bones.raccess.public)
        self.assertFalse(bones.raccess.published)
        self.assertFalse(bones.raccess.discoverable)
        self.assertTrue(bones.raccess.shareable)

        # should restore readwrite to owner
        self.assertTrue(dog.uaccess.owns_resource(bones))
        self.assertTrue(dog.uaccess.can_change_resource(bones))
        self.assertTrue(dog.uaccess.can_view_resource(bones))

    def test_08_public(self):
        """Public resources show up in public listings"""
        chewies = self.chewies
        dog = self.dog
        nobody = self.nobody

        self.assertFalse(chewies.raccess.immutable)
        self.assertFalse(chewies.raccess.public)
        self.assertFalse(chewies.raccess.published)
        self.assertFalse(chewies.raccess.discoverable)
        self.assertTrue(chewies.raccess.shareable)

        chewies.raccess.public = True
        chewies.raccess.save()

        self.assertFalse(chewies.raccess.immutable)
        self.assertTrue(chewies.raccess.public)
        self.assertFalse(chewies.raccess.published)
        self.assertFalse(chewies.raccess.discoverable)
        self.assertTrue(chewies.raccess.shareable)

        self.assertTrue(is_equal_to_as_set([chewies], GenericResource.public_resources.all()))
        self.assertTrue(is_equal_to_as_set([chewies], GenericResource.discoverable_resources.all()))

        # can 'nobody' see the public resource owned by 'dog'
        # but not explicitly shared with 'nobody'.
        self.assertTrue(nobody.uaccess.can_view_resource(chewies))
        self.assertFalse(nobody.uaccess.can_change_resource(chewies))
        self.assertFalse(nobody.uaccess.owns_resource(chewies))

    def test_08_discoverable(self):
        """Discoverable resources show up in discoverable resource listings"""
        chewies = self.chewies
        nobody = self.nobody

        # test making a resource public
        self.assertFalse(chewies.raccess.immutable)
        self.assertFalse(chewies.raccess.public)
        self.assertFalse(chewies.raccess.published)
        self.assertFalse(chewies.raccess.discoverable)
        self.assertTrue(chewies.raccess.shareable)

        chewies.raccess.discoverable = True
        chewies.raccess.save()

        self.assertFalse(chewies.raccess.immutable)
        self.assertFalse(chewies.raccess.public)
        self.assertFalse(chewies.raccess.published)
        self.assertTrue(chewies.raccess.discoverable)
        self.assertTrue(chewies.raccess.shareable)

        # discoverable doesn't mean public
        # TODO: get_public_resources and get_discoverable_resources should be static methods
        self.assertTrue(is_equal_to_as_set([], GenericResource.public_resources.all()))
        self.assertTrue(is_equal_to_as_set([chewies], GenericResource.discoverable_resources.all()))

        # can 'nobody' see the public resource owned by 'dog' but not explicitly shared with 'nobody'.
        self.assertFalse(nobody.uaccess.owns_resource(chewies))
        self.assertFalse(nobody.uaccess.can_change_resource(chewies))
        self.assertFalse(nobody.uaccess.can_view_resource(chewies))

    def test_09_retract(self):
        """Retracted resources cannot be accessed"""
        chewies = self.chewies
        resource_short_id = chewies.short_id
        hydroshare.delete_resource(chewies.short_id)
        with self.assertRaises(Http404):
            hydroshare.get_resource(resource_short_id)

