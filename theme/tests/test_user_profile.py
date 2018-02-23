from django.test import TestCase
from theme.models import UserProfile, User


class UserTestCase(TestCase):
    def setUp(self):
        User.objects.create(email="test@testing.com")

    def test_email_opt_out_default(self):
        user = UserProfile.objects.first()
        self.assertFalse(user.email_opt_out)
