import json
import uuid

from django.contrib.auth.models import Group
from django.urls import reverse

from hs_access_control.models import PrivilegeCodes
from hs_core import hydroshare
from hs_core.views import get_remaining_quota
from hs_core.testing import MockS3TestCaseMixin, ViewTestCase


class TestGetRemainingQuota(MockS3TestCaseMixin, ViewTestCase):
    def setUp(self):
        super(TestGetRemainingQuota, self).setUp()
        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.owner = hydroshare.create_account(
            'remaining_quota_owner@email.com',
            username='owner' + str(uuid.uuid4()),
            first_name='owner_first_name',
            last_name='owner_last_name',
            superuser=False,
            groups=[self.hs_group]
        )
        self.other = hydroshare.create_account(
            'remaining_quota_other@email.com',
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
        super(TestGetRemainingQuota, self).tearDown()

    def _get(self, user):
        url = reverse('get_remaining_quota', kwargs={'shortkey': self.res.short_id})
        request = self.factory.get(url)
        request.user = user
        self.add_session_to_request(request)
        return get_remaining_quota(request, shortkey=self.res.short_id)

    def test_returns_remaining_quota_of_quota_holder(self):
        uq = self.owner.quotas.first() or self.owner.quotas.create()
        uq.save_allocated_value(20, 'GB')

        response = self._get(self.owner)
        data = json.loads(response.content.decode())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertIsInstance(data['remaining_quota'], int)
        self.assertGreater(data['remaining_quota'], 0)
        self.assertLessEqual(data['remaining_quota'], 20 * 1024**3)

    def test_remaining_quota_is_zero_when_quota_is_used_up(self):
        uq = self.owner.quotas.first() or self.owner.quotas.create()
        uq.save_allocated_value(0, 'GB')

        response = self._get(self.owner)
        data = json.loads(response.content.decode())

        self.assertEqual(data['remaining_quota'], 0)

    def test_viewer_gets_quota_holder_quota(self):
        uq = self.owner.quotas.first() or self.owner.quotas.create()
        uq.save_allocated_value(0, 'GB')
        self.owner.uaccess.share_resource_with_user(self.res, self.other, PrivilegeCodes.VIEW)

        response = self._get(self.other)
        data = json.loads(response.content.decode())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['remaining_quota'], 0)

    def test_user_without_view_access_is_denied(self):
        response = self._get(self.other)
        self.assertEqual(response.status_code, 403)
