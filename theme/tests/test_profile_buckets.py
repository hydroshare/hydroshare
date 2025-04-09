from django.test import TestCase
from theme.models import UserProfile
from hs_core import hydroshare
from django.contrib.auth.models import Group


def create_user_profile(username):
    Group.objects.get_or_create(name="Hydroshare Author")
    hydroshare.create_account(
        f"{username}@gmail.com",
        username=username,
        first_name="Test",
        last_name="User",
        user_type="University Faculty",
        country="United States",
        state="NC",
    )
    return UserProfile.objects.filter(user__username=username).first()


class TestUserProfileBuckets(TestCase):
    def setUp(self):
        username = "testuser"
        create_user_profile(username)
        self.user_profile = UserProfile.objects.filter(user__username=username).first()

    def test_bucket_name_initial_value(self):
        new_user_profile = create_user_profile("new_testuser")
        self.assertEqual(new_user_profile.bucket_name, "newtestuser")

    def test_bucket_name_gets_set_during_user_profile_creation(self):
        self.assertEqual(self.user_profile._bucket_name, "testuser")

    def test_bucket_name_immutable(self):
        with self.assertRaises(AttributeError):
            self.user_profile.bucket_name = "renamed"
            self.user_profile.save()

        # refresh the user_profile object
        self.user_profile.refresh_from_db()

        # see that the bucket_name attribute is still the same
        self.assertEqual(self.user_profile.bucket_name, "testuser")

    def test_fail(self):
        self.assertEqual(True, False)
