import json
import uuid

from django.conf import settings
from django.contrib.auth.models import Group
from django.urls import reverse

from hs_core import hydroshare
from hs_core.views import get_upload_limits
from hs_core.testing import MockS3TestCaseMixin, ViewTestCase


class TestGetUploadLimits(MockS3TestCaseMixin, ViewTestCase):
    def setUp(self):
        super(TestGetUploadLimits, self).setUp()
        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.owner = hydroshare.create_account(
            'upload_limits_owner@email.com',
            username='owner' + str(uuid.uuid4()),
            first_name='owner_first_name',
            last_name='owner_last_name',
            superuser=False,
            groups=[self.hs_group]
        )
        self.other = hydroshare.create_account(
            'upload_limits_other@email.com',
            username='other' + str(uuid.uuid4()),
            first_name='other_first_name',
            last_name='other_last_name',
            superuser=False,
            groups=[self.hs_group]
        )
        self.res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.owner,
            title='My Test Resource'
        )

    def tearDown(self):
        hydroshare.delete_resource(self.res.short_id)
        super(TestGetUploadLimits, self).tearDown()

    def _get(self, user):
        url = reverse('get_upload_limits', kwargs={'shortkey': self.res.short_id})
        request = self.factory.get(url)
        request.user = user
        self.add_session_to_request(request)
        return get_upload_limits(request, shortkey=self.res.short_id)

    def test_returns_limits_and_remaining_quota_of_quota_holder(self):
        uq = self.owner.quotas.first() or self.owner.quotas.create()
        uq.save_allocated_value(20, 'GB')

        response = self._get(self.owner)
        data = json.loads(response.content.decode())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['max_file_size'], settings.FILE_UPLOAD_MAX_SIZE)
        self.assertEqual(data['max_number_of_files'], settings.MAX_NUMBER_OF_FILES_IN_SINGLE_LOCAL_UPLOAD)
        self.assertIsInstance(data['remaining_quota'], int)
        self.assertGreater(data['remaining_quota'], 0)
        self.assertLessEqual(data['remaining_quota'], 20 * 1024**3)

    def test_remaining_quota_is_zero_when_quota_is_used_up(self):
        uq = self.owner.quotas.first() or self.owner.quotas.create()
        uq.save_allocated_value(0, 'GB')

        response = self._get(self.owner)
        data = json.loads(response.content.decode())

        self.assertEqual(data['remaining_quota'], 0)

    def test_user_without_edit_access_is_denied(self):
        response = self._get(self.other)
        self.assertEqual(response.status_code, 403)
