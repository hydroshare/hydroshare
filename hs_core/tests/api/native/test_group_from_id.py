
from __future__ import absolute_import

from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core import hydroshare


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
        self.group = self.user.uaccess.create_group('Jamy group')

    def test_accept_group_instance(self):
        self.assertEquals(
            hydroshare.group_from_id(self.group),
            self.group,
            msg='group did not match'
        )

    def test_accept_group_name(self):
        self.assertEqual(
            hydroshare.group_from_id(self.group.name),
            self.group,
            msg='lookup group name failed'
        )

    def test_accept_group_pk(self):
        self.assertEqual(
            hydroshare.group_from_id(self.group.pk),
            self.group,
            msg='lookup group id failed'
        )