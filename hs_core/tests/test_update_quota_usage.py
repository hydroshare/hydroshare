from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from unittest.mock import patch

from theme.models import UserQuota
from hs_core.tasks import update_quota_usage


class UpdateQuotaUsageTestCase(TestCase):
    # TODO: revamp these tests and add more tests

    def setUp(self):
        self.username = 'testuser'
        self.hs_internal_zone = 'hydroshare'
        self.user = User.objects.create_user(username=self.username, password='password', email='email')

    @patch('hs_core.tasks.get_quota_usage')
    @patch('hs_core.tasks.get_storage_usage')
    def test_update_quota_usage(self, mock_get_storage_usage, mock_get_quota_usage):
        mock_get_quota_usage.return_value = (100, 200)  # Mocking the return values of get_quota_usage
        mock_get_storage_usage.return_value = 50  # Mocking the return value of get_storage_usage

        # Create a UserQuota object for the user in the hydroshare zone
        UserQuota.objects.create(user=self.user, zone=self.hs_internal_zone)

        # Call the update_quota_usage function
        update_quota_usage(self.username)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)

        # Assert that the used values have been updated correctly
        self.assertEqual(user_quota.user_zone_value, 100)
        self.assertEqual(user_quota.data_zone_value, 150)

    def test_update_quota_usage_quota_row_not_found(self):
        # Call the update_quota_usage function when the quota row does not exist
        with self.assertRaises(ValidationError):
            update_quota_usage(self.username)

    def test_adding_file_increase_quota(self):
        # Create a UserQuota object for the user in the hydroshare zone
        UserQuota.objects.create(user=self.user, zone=self.hs_internal_zone)

        # Call the update_quota_usage function
        update_quota_usage(self.username)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)

        # Assert that the used values have been updated correctly
        self.assertEqual(user_quota.used_value_user_zone, 0)
        self.assertEqual(user_quota.used_value_data_zone, 0)

        # Create a file with size 100
        file_size = 100

        # Call the update_quota_usage function
        update_quota_usage(self.username, file_size)

        # Retrieve the UserQuota object for the user
        user_quota = UserQuota.objects.get(user=self.user, zone=self.hs_internal_zone)

        # Assert that the used values have been updated correctly
        self.assertEqual(user_quota.used_value_user_zone, 100)
        self.assertEqual(user_quota.used_value_data_zone, 0)
