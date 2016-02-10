__author__ = 'shaunjl'

"""
comments- not sure how to implement test_email_function

"""

import unittest

from django.contrib.auth.models import User, Group
from django.test import TestCase

from hs_core import hydroshare


class CreateAccountTest(TestCase):
    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

    def test_basic_superuser(self):
        username, first_name, last_name, password = 'shaunjl', 'shaun','joseph','mypass'
        user = hydroshare.create_account(
            'shaun@gmail.com',
            username=username,
            first_name=first_name,
            last_name=last_name,
            superuser=True,
            password=password,
            active=True
            )

        users_in_db = User.objects.all()
        db_user = users_in_db[0]
        self.assertEqual(user.email, db_user.email)
        self.assertEqual(user.username, db_user.username)
        self.assertEqual(user.first_name, db_user.first_name)
        self.assertEqual(user.last_name, db_user.last_name)
        self.assertEqual(user.password, db_user.password)
        self.assertEqual(user.is_superuser, db_user.is_superuser)
        self.assertEqual(user.is_active, db_user.is_active)
        self.assertTrue(db_user.is_active)
        self.assertTrue(user.is_active)
        self.assertTrue(db_user.is_superuser)
        self.assertTrue(user.is_superuser)

    def test_basic_user(self):
        username, first_name, last_name, password = 'shaunjl', 'shaun','joseph','mypass'
        user = hydroshare.create_account(
            'shaun@gmail.com',
            username=username,
            first_name=first_name,
            last_name=last_name,
            superuser=False,
            password=password,
            active=True
            )

        users_in_db = User.objects.all()
        db_user = users_in_db[0]
        self.assertEqual(user.email, db_user.email)
        self.assertEqual(user.username, db_user.username)
        self.assertEqual(user.first_name, db_user.first_name)
        self.assertEqual(user.last_name, db_user.last_name)
        self.assertEqual(user.password, db_user.password)
        self.assertEqual(user.is_superuser, db_user.is_superuser)
        self.assertEqual(user.is_active, db_user.is_active)
        self.assertTrue(db_user.is_active)
        self.assertTrue(user.is_active)
        self.assertFalse(db_user.is_superuser)
        self.assertFalse(user.is_superuser)

    def test_with_groups(self):
        groups = []

        username, first_name, last_name, password = 'shaunjl', 'shaun', 'joseph', 'mypass'
        user = hydroshare.create_account(
            'shaun@gmail.com',
            username=username,
            first_name=first_name,
            last_name=last_name,
            groups=groups
            )

        g0 = user.uaccess.create_group('group0')
        g1 = user.uaccess.create_group('group1')
        g2 = user.uaccess.create_group('group2')

        # TODO from @alvacouch: no order assumption -> poor test. 
        user_groups = list(Group.objects.filter(g2ugp__user=user))

        groups = [g0, g1, g2]

        self.assertEqual(groups, user_groups)

    @unittest.skip
    def test_email_function(self):
        pass
