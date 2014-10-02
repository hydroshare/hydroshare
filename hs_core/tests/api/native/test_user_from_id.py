## test case for user_from_id API Tian Gan
# the first 3 test functions are similar from the original test_utils.py
# add one test function : test_accept_user_pk(self)

from __future__ import absolute_import
from unittest import TestCase
from hs_core import hydroshare
from django.contrib.auth.models import User


class TestUserFromId(TestCase):
    def setUp(self):
        self.user = hydroshare.create_account(
            'jamy2@gmail.com',
            username='jamy2',
            first_name='Tian',
            last_name='Gan',
            superuser=False,
            groups=[]
        )

    def tearDown(self):
        User.objects.all().delete()

    def test_accept_user_instance(self):
        self.assertEquals(
            hydroshare.user_from_id(self.user),
            self.user,
            msg='user passthrough failed',
        )

    def test_accept_user_name(self):
        self.assertEqual(
            hydroshare.user_from_id(self.user.username),
            self.user,
            msg='lookup by user name failed'
        )

    def test_accept_user_email(self):
        self.assertEqual(
            hydroshare.user_from_id(self.user.email),
            self.user,
            msg='lookup by user email failed'
        )

    def test_accept_user_pk(self):
        self.assertEqual(
            hydroshare.user_from_id(self.user.pk),
            self.user,
            msg='lookup by user id failed'
        )





