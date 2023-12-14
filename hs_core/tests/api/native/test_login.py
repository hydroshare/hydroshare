from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core import hydroshare
from django.contrib.auth import (
    authenticate,
)


class CreateAccountTest(TestCase):
    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

    def test_login_case_insensitive_username(self):
        username, first_name, last_name, password = 'Shaunjl', 'shaun', 'joseph', 'mypass'
        hydroshare.create_account(
            'sHaun@gmail.com',
            username=username,
            first_name=first_name,
            last_name=last_name,
            superuser=False,
            password=password,
            active=True
        )

        user = authenticate(username="SHaUn@gmail.com", password="mypass")
        self.assertNotEqual(None, user)
        self.assertEqual(user.email, "sHaun@gmail.com")
        self.assertEqual(user.username, "Shaunjl")

    def test_login_case_insensitive_email(self):
        username, first_name, last_name, password = 'Shaunjl', 'shaun', 'joseph', 'mypass'
        hydroshare.create_account(
            'shaun@gmail.com',
            username=username,
            first_name=first_name,
            last_name=last_name,
            superuser=False,
            password=password,
            active=True
        )

        user = authenticate(username="ShAuNjl", password="mypass")
        self.assertNotEqual(None, user)
        self.assertEqual(user.email, "shaun@gmail.com")
        self.assertEqual(user.username, "Shaunjl")
