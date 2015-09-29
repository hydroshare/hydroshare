## test case for group_from_id API  Tian Gan
## the first 3 test functions are similar from the test_utils.py
## add the test_accept_group_pk(self) test function

from __future__ import absolute_import
import unittest
from unittest import TestCase

from hs_core import hydroshare
from hs_core.models import GenericResource
from django.contrib.auth.models import Group, User


class TestGroupFromId(TestCase):
    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'jamy1@gmail.com',
            username='jamy1',
            first_name='Tian',
            last_name='Gan',
            superuser=False,
            groups=[]
        )

        self.group = hydroshare.create_group(
            'Jamy group',
            members=[self.user],
            owners=[self.user]
        )

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()

    def test_accept_group_instance(self):
        self.assertEquals(
            hydroshare.group_from_id(self.group),
            self.group,
            msg='group passthrough failed'
        )

    @unittest.skip
    def test_accept_group_name(self):
        self.assertEqual(
            hydroshare.group_from_id(self.group.name),
            self.group,
            msg='lookup group name failed'
        )

    @unittest.skip
    def test_accept_group_pk(self):
        self.assertEqual(
            hydroshare.group_from_id(self.group.pk),
            self.group,
            msg='lookup group id failed'
        )