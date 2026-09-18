import json
import uuid

from django.contrib.auth.models import Group
from django.urls import reverse

from hs_core import hydroshare
from hs_core.views import change_quota_holder
from hs_core.testing import MockS3TestCaseMixin, ViewTestCase
from hs_access_control.models import PrivilegeCodes


class TestChangeQuotaHolder(MockS3TestCaseMixin, ViewTestCase):
    def setUp(self):
        super(TestChangeQuotaHolder, self).setUp()
        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create two users
        self.user1 = hydroshare.create_account(
            'test_user1@email.com',
            username='owner1' + str(uuid.uuid4()),
            first_name='owner1_first_name',
            last_name='owner1_last_name',
            superuser=False,
            groups=[self.hs_group]
        )
        self.user2 = hydroshare.create_account(
            'test_user2@email.com',
            username='owner2' + str(uuid.uuid4()),
            first_name='owner2_first_name',
            last_name='owner2_last_name',
            superuser=False,
            groups=[self.hs_group]
        )
        self.res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user1,
            title='My Test Resource'
        )
        # test to make sure one owner can transfer quota holder to another owner
        self.user1.uaccess.share_resource_with_user(self.res, self.user2, PrivilegeCodes.OWNER)

    def test_change_quota_holder(self):
        # here we are testing the change_quota_holder view function
        url_params = {'shortkey': self.res.short_id}
        url = reverse('change_quota_holder', kwargs=url_params)
        request = self.factory.post(url, data={'new_holder_username': self.user2.username})
        request.user = self.user1

        self.add_session_to_request(request)
        response = change_quota_holder(request, shortkey=self.res.short_id)
        response_data = json.loads(response.content.decode())
        self.res.refresh_from_db()
        self.assertTrue(self.res.quota_holder == self.user2)
        self.assertEqual(response_data['status'], 'success')

        # clean up
        hydroshare.delete_resource(self.res.short_id)

    def test_change_quota_holder_permission_denied_message_surfaced(self):
        # a non-owner attempting to become quota holder should surface the specific
        # PermissionDenied message raised by set_quota_holder, not a generic one
        self.user3 = hydroshare.create_account(
            'test_user3@email.com',
            username='nonowner' + str(uuid.uuid4()),
            first_name='nonowner_first_name',
            last_name='nonowner_last_name',
            superuser=False,
            groups=[self.hs_group]
        )
        url_params = {'shortkey': self.res.short_id}
        url = reverse('change_quota_holder', kwargs=url_params)
        request = self.factory.post(url, data={'new_holder_username': self.user3.username})
        request.user = self.user1

        self.add_session_to_request(request)
        response = change_quota_holder(request, shortkey=self.res.short_id)
        response_data = json.loads(response.content.decode())
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(
            response_data['message'],
            "Only owners can set or be set as quota holder for the resource"
        )

    def test_change_quota_holder_community_restriction_message_surfaced(self):
        # when the new holder's UserQuota has a required_community_membership set and the
        # requesting user (setter) does not belong to a qualifying group, the community-specific
        # message should be surfaced
        community = self.user1.uaccess.create_community(
            'Required Community',
            'A community used to restrict quota holder changes.'
        )
        community.active = True
        community.save()

        user_quota = self.user2.quotas.get()
        user_quota.required_community_membership = community
        user_quota.save()

        url_params = {'shortkey': self.res.short_id}
        url = reverse('change_quota_holder', kwargs=url_params)
        request = self.factory.post(url, data={'new_holder_username': self.user2.username})
        request.user = self.user1

        self.add_session_to_request(request)
        response = change_quota_holder(request, shortkey=self.res.short_id)
        response_data = json.loads(response.content.decode())
        self.assertEqual(response_data['status'], 'error')
        self.assertEqual(
            response_data['message'],
            "New quota holder can only be set by a user who "
            f"belongs to a group in the community '{community.name}'"
        )
