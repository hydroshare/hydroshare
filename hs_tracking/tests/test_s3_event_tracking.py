from contextlib import nullcontext
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from hs_event_s3.tasks import record_s3_download


class S3EventTrackingTests(SimpleTestCase):
    @patch("hs_event_s3.tasks.Session.objects.create")
    @patch("hs_event_s3.tasks.Visitor.objects.get_or_create")
    @patch("hs_event_s3.tasks.User.objects.get")
    @patch("hs_event_s3.tasks._link_s3_file_to_resource")
    @patch("hs_event_s3.tasks.delete_resource_file")
    def test_get_object_records_s3_activity_without_mutating_resource(
        self, delete_file, link_file, get_user, get_or_create_visitor, create_session
    ):
        resource_id = "a" * 32
        user = Mock()
        visitor = Mock()
        session = Mock()
        get_user.return_value = user
        get_or_create_visitor.return_value = (visitor, False)
        create_session.return_value = session

        with patch("hs_event_s3.tasks.transaction.atomic", return_value=nullcontext()):
            record_s3_download.run(
                action="s3:GetObject",
                bucket="resource",
                object_path=f"{resource_id}/data/contents/example.csv",
                username="testuser",
                user_id=42,
            )

        get_user.assert_called_once_with(pk=42)
        get_or_create_visitor.assert_called_once_with(user=user)
        create_session.assert_called_once_with(visitor=visitor)
        session.record.assert_called_once_with(
            "s3",
            value=f"s3_action=s3:GetObject|resource_guid={resource_id}|bucket=resource",
            resource_id=resource_id,
        )
        link_file.assert_not_called()
        delete_file.assert_not_called()

    @patch("hs_event_s3.tasks.User.objects.get")
    def test_invalid_download_event_is_ignored(self, get_user):
        record_s3_download.run(
            action="s3:DeleteObject",
            bucket="resource",
            object_path=f"{'a' * 32}/data/contents/example.csv",
            username="testuser",
            user_id=42,
        )

        get_user.assert_not_called()
