from django.test import TestCase
from theme.models import UserProfile
from hs_core import hydroshare
from django.contrib.auth.models import Group


def create_user_profile(username):
    Group.objects.get_or_create(name="Hydroshare Author")
    user = hydroshare.create_account(
        f"{username}@gmail.com",
        username=username,
        first_name="Test",
        last_name="User",
        user_type="University Faculty",
        country="United States",
        state="NC",
    )
    return UserProfile.objects.filter(user=user).first()


class TestUserProfileBuckets(TestCase):
    def setUp(self):
        username = "testuser"
        create_user_profile(username)
        self.user_profile = UserProfile.objects.filter(user__username=username).first()

    def test_bucket_name_initial_value(self):
        new_user_profile = create_user_profile("new_testuser")
        self.assertIsNone(new_user_profile._bucket_name)

    def test_bucket_name_immutable(self):
        self.user_profile._bucket_name = "bucket"
        self.user_profile.save()
        self.assertEqual(self.user_profile._bucket_name, "bucket")

        self.user_profile._bucket_name = "renamed"
        self.user_profile.save()

        # refresh the user_profile object
        self.user_profile.refresh_from_db()

        # see that the bucket_name attribute is still the same
        self.assertEqual(self.user_profile._bucket_name, "bucket")

    def test_bucket_name_set_from_property_immutable(self):
        self.user_profile.bucket_name
        self.user_profile.save()
        self.assertEqual(self.user_profile._bucket_name, "testuser")

        self.user_profile._bucket_name = "new_bucket"
        self.user_profile.save()

        # refresh the user_profile object
        self.user_profile.refresh_from_db()

        # see that the bucket_name attribute is still the same
        self.assertEqual(self.user_profile.bucket_name, "testuser")
