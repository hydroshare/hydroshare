from django.test import TestCase
from theme.models import User
from django.core.exceptions import ValidationError


class ForceUniqueEmails(TestCase):

    def test_force_unique_emails(self):
        User.objects.create(email="test@testing.com")
        try:
            User.objects.create(email="test@testing.com")
            self.fail("Should have thrown validation error for duplicate email")
        except Exception as e:
            self.assertTrue(isinstance(e, ValidationError))

    def test_force_email_required(self):
        try:
            User.objects.create()
            self.fail("Should have thrown ValidationError, email is required")
        except Exception as e:
            self.assertTrue(isinstance(e, ValidationError))

    def test_duplicate_username(self):
        User.objects.create(email="test@testing.com", username="scoot")
        try:
            User.objects.create(email="different@testing.com", username="scoot")
            self.fail("Should have thrown ValidationError, duplicate username")
        except Exception as e:
            self.assertTrue(isinstance(e, ValidationError))
