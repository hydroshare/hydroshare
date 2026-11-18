from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from hs_event_s3.tasks import process_s3_event


class S3EventSizeCacheTest(SimpleTestCase):
    @patch('hs_event_s3.tasks.UserQuota.objects.get')
    @patch('hs_event_s3.tasks._link_s3_file_to_resource')
    @patch('hs_event_s3.tasks.BaseResource.objects.get')
    def test_write_refreshes_file_size(self, get_resource, link_file, get_quota):
        resource = get_resource.return_value
        resource.quota_holder = Mock()
        resource_file = link_file.return_value
        process_s3_event.run('s3:PutObject', 'bucket', 'resource-id/data/contents/file.txt', 'user', 1)
        link_file.assert_called_once_with(resource, 'file.txt')
        resource_file.calculate_size.assert_called_once_with(resource=resource)
        get_quota.assert_called_once_with(user=resource.quota_holder)
