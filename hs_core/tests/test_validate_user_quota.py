import uuid
from unittest.mock import patch, MagicMock
from django.test import TestCase
from hs_core.exceptions import QuotaException
from hs_core.hydroshare.utils import validate_user_quota
from theme.models import QuotaMessage, UserQuota
from django.contrib.auth.models import User, Group
from hs_core import hydroshare
from hs_core.models import BaseResource


class ValidateUserQuotaTestCase(TestCase):
    """Test cases for validate_user_quota function"""

    def setUp(self):
        self.username = 'testuser'
        self.hs_internal_zone = 'hydroshare'
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username=self.username + uuid.uuid4().hex,  # to ensure unique bucket in minio
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.group]
        )

        # Create a default quota message
        self.quota_message = QuotaMessage.objects.create(
            enforce_content_prepend="Quota exceeded: ",
            content="You have used {used} {unit} out of {allocated} {unit} in {zone} ({percent}%)."
        )

        # Mock the MinIO interactions for all tests
        self.mock_subprocess = patch('theme.models.subprocess.run').start()
        self.addCleanup(patch.stopall)

    def tearDown(self):
        super(ValidateUserQuotaTestCase, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()
        Group.objects.all().delete()
        UserQuota.objects.all().delete()
        QuotaMessage.objects.all().delete()
        patch.stopall()

    def _mock_quota_info(self, allocated_size, unit):
        """Mock the quota info response from MinIO"""
        mock_result = MagicMock()
        # size_with_unit_str = result.stdout.split("Total size: ")[1].split("\n")[0]
        mock_result.stdout = f"Total size: {allocated_size} {unit}"
        mock_result.stderr = ""
        mock_result.returncode = 0
        return mock_result

    def _mock_stat_info(self, used_size, unit):
        """Mock the stat info response from MinIO with proper format"""
        mock_result = MagicMock()
        # The actual format from mc stat command includes "Total size: " prefix
        mock_result.stdout = f"Total size: {used_size} {unit}"
        mock_result.stderr = ""
        mock_result.returncode = 0
        return mock_result

    def test_validate_user_quota_none_user(self):
        """Test that no exception is raised when user is None"""
        # Should not raise any exception
        try:
            validate_user_quota(None, 1000)
            self.assertTrue(True)  # If we reach here, test passes
        except Exception as e:
            self.fail(f"validate_user_quota raised unexpected exception: {e}")

    def test_validate_user_quota_nonexistent_user(self):
        """Test that no exception is raised when username doesn't exist"""
        # Should not raise any exception
        try:
            validate_user_quota("nonexistent_user", 1000)
            self.assertTrue(True)  # If we reach here, test passes
        except Exception as e:
            self.fail(f"validate_user_quota raised unexpected exception: {e}")

    @patch('hs_core.hydroshare.utils.convert_file_size_to_unit')
    def test_validate_user_quota_within_quota(self, mock_convert):
        """Test that no exception is raised when user is within quota"""
        # Set up the mock to return different values for different calls
        self.mock_subprocess.side_effect = [
            self._mock_quota_info(100, "MB"),  # First call for allocated_value
            self._mock_stat_info(50, "MB"),    # Second call for used_value
            self._mock_quota_info(100, "MB"),  # Third call for unit
        ]

        # Mock the conversion to return 25MB (the size we're adding)
        mock_convert.return_value = 25

        # Adding 25MB should be within quota (50 + 25 = 75 < 100)
        try:
            validate_user_quota(self.user, 25 * 1024 * 1024)  # 25MB in bytes
            self.assertTrue(True)  # If we reach here, test passes
        except Exception as e:
            self.fail(f"validate_user_quota raised unexpected exception: {e}")

    def test_validate_user_quota_exactly_at_quota(self):
        """Test that exception is raised when user exactly reaches quota limit"""
        # Set up the mock to return different values for different calls
        self.mock_subprocess.side_effect = self._mock_quota_info(100, "MB")

        # Adding exactly 50MB should exceed quota (50 + 50 = 100 >= 100)
        with self.assertRaises(QuotaException) as context:
            validate_user_quota(self.user, 50 * 1024 * 1024)  # 50MB in bytes

        exception_message = str(context.exception)
        self.assertIn("Quota exceeded", exception_message)

    @patch('hs_core.hydroshare.utils.convert_file_size_to_unit')
    def test_validate_user_quota_over_quota(self, mock_convert):
        """Test that exception is raised when user exceeds quota"""
        # Set up the mock to return different values for different calls
        self.mock_subprocess.side_effect = [
            self._mock_quota_info(100, "MB"),  # First call for allocated_value
            self._mock_stat_info(80, "MB"),    # Second call for used_value
            self._mock_quota_info(100, "MB"),  # Third call for unit
        ]

        # Mock the conversion to return 30MB (the size we're adding)
        mock_convert.return_value = 30

        # Adding 30MB should exceed quota (80 + 30 = 110 > 100)
        with self.assertRaises(QuotaException) as context:
            validate_user_quota(self.user, 30 * 1024 * 1024)  # 30MB in bytes

        exception_message = str(context.exception)
        self.assertIn("Quota exceeded", exception_message)

    def test_validate_user_quota_no_quota_object(self):
        """Test that no exception is raised when user has no quota object"""
        # Delete the quota object
        UserQuota.objects.all().delete()

        # User has no quota object, should not raise exception
        try:
            validate_user_quota(self.user, 1000)
            self.assertTrue(True)  # If we reach here, test passes
        except Exception as e:
            self.fail(f"validate_user_quota raised unexpected exception: {e}")

    @patch('hs_core.hydroshare.utils.convert_file_size_to_unit')
    def test_validate_user_quota_no_quota_message(self, mock_convert):
        """Test behavior when no QuotaMessage exists"""
        # Delete the quota message
        QuotaMessage.objects.all().delete()

        # Set up the mock to return different values for different calls
        self.mock_subprocess.side_effect = [
            self._mock_quota_info(10, "MB"),  # First call for allocated_value
            self._mock_stat_info(5, "MB"),    # Second call for used_value
            self._mock_quota_info(10, "MB"),  # Third call for unit
        ]

        # Mock the conversion to return 20MB (the size we're adding)
        mock_convert.return_value = 20

        # Should still raise QuotaException even without QuotaMessage
        with self.assertRaises(QuotaException):
            validate_user_quota(self.user, 20 * 1024 * 1024)  # 20MB in bytes

    # @patch('hs_core.hydroshare.utils.convert_file_size_to_unit')
    # def test_validate_user_quota_different_units(self, mock_convert):
    #     """Test quota validation with different units"""
    #     # Set up the mock to return different values for different calls
    #     self.mock_subprocess.side_effect = [
    #         self._mock_quota_info(0.5, "GB"),  # First call for allocated_value
    #         self._mock_stat_info(0.1, "GB"),   # Second call for used_value
    #         self._mock_quota_info(0.5, "GB"),  # Third call for unit
    #     ]

    #     # Mock the conversion to return 0.6GB (the size we're adding)
    #     mock_convert.return_value = 0.6

    #     # Adding 0.6GB should exceed quota (0.1 + 0.6 = 0.7 > 0.5)
    #     with self.assertRaises(QuotaException):
    #         validate_user_quota(self.user, 0.6 * 1024 * 1024 * 1024)  # 0.6GB in bytes

    @patch('hs_core.hydroshare.utils.convert_file_size_to_unit')
    def test_validate_user_quota_with_username_string(self, mock_convert):
        """Test that function works with username string instead of User object"""
        # Set up the mock to return different values for different calls
        self.mock_subprocess.side_effect = [
            self._mock_quota_info(100, "MB"),  # First call for allocated_value
            self._mock_stat_info(90, "MB"),    # Second call for used_value
            self._mock_quota_info(100, "MB"),  # Third call for unit
        ]

        # Mock the conversion to return 20MB (the size we're adding)
        mock_convert.return_value = 20

        # Should raise exception when passing username string
        with self.assertRaises(QuotaException):
            validate_user_quota(self.user.username, 20 * 1024 * 1024)  # 20MB in bytes

    @patch('hs_core.hydroshare.utils.convert_file_size_to_unit')
    def test_validate_user_quota_zero_size(self, mock_convert):
        """Test that zero size doesn't affect quota validation"""
        # Set up the mock to return different values for different calls
        self.mock_subprocess.side_effect = [
            self._mock_quota_info(100, "MB"),  # First call for allocated_value
            self._mock_stat_info(99, "MB"),    # Second call for used_value
            self._mock_quota_info(100, "MB"),  # Third call for unit
        ]

        # Mock the conversion to return 0 (the size we're adding)
        mock_convert.return_value = 0

        # Adding zero size should not raise exception
        try:
            validate_user_quota(self.user, 0)
            self.assertTrue(True)  # If we reach here, test passes
        except Exception as e:
            self.fail(f"validate_user_quota raised unexpected exception for zero size: {e}")

    @patch('hs_core.hydroshare.utils.convert_file_size_to_unit')
    def test_validate_user_quota_negative_size(self, mock_convert):
        """Test that negative size doesn't affect quota validation"""
        # Set up the mock to return different values for different calls
        self.mock_subprocess.side_effect = [
            self._mock_quota_info(100, "MB"),  # First call for allocated_value
            self._mock_stat_info(50, "MB"),    # Second call for used_value
            self._mock_quota_info(100, "MB"),  # Third call for unit
        ]

        # Mock the conversion to return 0 (negative size treated as zero)
        mock_convert.return_value = 0

        # Adding negative size should not raise exception (treated as zero)
        try:
            validate_user_quota(self.user, -1000)
            self.assertTrue(True)  # If we reach here, test passes
        except Exception as e:
            self.fail(f"validate_user_quota raised unexpected exception for negative size: {e}")