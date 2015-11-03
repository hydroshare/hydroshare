"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class AccountTests(TestCase):

    def make_user(self, username="user", email="user@example.com", **kwargs):
        return User.objects.create(username=username, email=email, **kwargs)

    def test_unique_email(self):
        self.make_user(username="user1")
        self.assertRaises(ValidationError, self.make_user, username="user2")
