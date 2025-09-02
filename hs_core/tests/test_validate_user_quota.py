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

        # Create UserQuota for the user
        self.user_quota, _ = UserQuota.objects.get_or_create(
            user=self.user,
            zone=self.hs_internal_zone
        )

        # Set up individual test mocks
        self.mock_subprocess_patcher = patch('theme.models.subprocess.run')
        self.mock_subprocess = self.mock_subprocess_patcher.start()

    def tearDown(self):
        # Stop all patches
        self.mock_subprocess_patcher.stop()
        self.mock_subprocess.reset_mock()

        # Clean up database
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()
        UserQuota.objects.all().delete()
        QuotaMessage.objects.all().delete()
        super().tearDown()

    def _mock_minio_info(self, allocated_size, unit):
        """Mock the quota info response from MinIO"""
        mock_result = MagicMock()
        # size_with_unit_str = result.stdout.split("Total size: ")[1].split("\n")[0]
        mock_result.stdout = f"Total size: {allocated_size} {unit}"
        mock_result.stderr = ""
        mock_result.returncode = 0
        return mock_result

    def _setup_mock_side_effect(self, allocated_size, allocated_unit, used_size, used_unit):
        """Setup mock side effect function for subprocess calls"""
        def side_effect_func(*args, **kwargs):
            cmd = ' '.join(args[0])
            if 'quota' in cmd:
                return self._mock_minio_info(allocated_size, allocated_unit)
            elif 'stat' in cmd:
                return self._mock_minio_info(used_size, used_unit)
            return MagicMock()

        self.mock_subprocess.side_effect = side_effect_func

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

    def test_validate_user_quota_within_quota(self):
        """Test that no exception is raised when user is within quota"""
        # Setup mock responses
        self._setup_mock_side_effect(100, "MB", 50, "MB")

        # Adding 25MB should be within quota (50 + 25 = 75 < 100)
        try:
            validate_user_quota(self.user, 25 * 1024 * 1024)  # 25MB in bytes
            self.assertTrue(True)  # If we reach here, test passes
        except Exception as e:
            self.fail(f"validate_user_quota raised unexpected exception: {e}")

    def test_validate_user_quota_exactly_at_quota(self):
        """Test that exception is raised when user exactly reaches quota limit"""
        # Setup mock responses
        self._setup_mock_side_effect(100, "MB", 50, "MB")

        # Adding exactly 50MB should exceed quota (50 + 50 = 100 >= 100)
        with self.assertRaises(QuotaException) as context:
            validate_user_quota(self.user, 50 * 1024 * 1024)  # 50MB in bytes

        exception_message = str(context.exception)
        self.assertIn("Quota exceeded", exception_message)

    def test_validate_user_quota_over_quota(self):
        """Test that exception is raised when user exceeds quota"""
        # Setup mock responses
        self._setup_mock_side_effect(100, "MB", 80, "MB")

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

    def test_validate_user_quota_no_quota_message(self):
        """Test behavior when no QuotaMessage exists"""
        # Delete the quota message
        QuotaMessage.objects.all().delete()

        # Setup mock responses
        self._setup_mock_side_effect(10, "MB", 5, "MB")

        # Should still raise QuotaException even without QuotaMessage
        with self.assertRaises(QuotaException):
            validate_user_quota(self.user, 20 * 1024 * 1024)  # 20MB in bytes

    def test_validate_user_quota_with_username_string(self):
        """Test that function works with username string instead of User object"""
        # Setup mock responses
        self._setup_mock_side_effect(100, "MB", 90, "MB")

        # Should raise exception when passing username string
        with self.assertRaises(QuotaException):
            validate_user_quota(self.user.username, 20 * 1024 * 1024)  # 20MB in bytes

    def test_validate_user_quota_zero_size(self):
        """Test that zero size doesn't affect quota validation"""
        # Setup mock responses
        self._setup_mock_side_effect(100, "MB", 99, "MB")

        # Adding zero size should not raise exception
        try:
            validate_user_quota(self.user, 0)
            self.assertTrue(True)  # If we reach here, test passes
        except Exception as e:
            self.fail(f"validate_user_quota raised unexpected exception for zero size: {e}")

    def test_validate_user_quota_negative_size(self):
        """Test that negative size doesn't affect quota validation"""
        # Setup mock responses
        self._setup_mock_side_effect(100, "MB", 50, "MB")

        # Adding negative size should not raise exception (treated as zero)
        try:
            validate_user_quota(self.user, -1000)
            self.assertTrue(True)  # If we reach here, test passes
        except Exception as e:
            self.fail(f"validate_user_quota raised unexpected exception for negative size: {e}")
