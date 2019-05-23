import json

from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse

from hs_core import hydroshare
from hs_core.views import change_quota_holder
from hs_core.testing import MockIRODSTestCaseMixin, ViewTestCase
from hs_access_control.models import PrivilegeCodes


class TestChangeQuotaHolder(MockIRODSTestCaseMixin, ViewTestCase):
    def setUp(self):
        super(TestChangeQuotaHolder, self).setUp()
        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create two users
        self.user1 = hydroshare.create_account(
            'test_user1@email.com',
            username='owner1',
            first_name='owner1_first_name',
            last_name='owner1_last_name',
            superuser=False,
            groups=[self.hs_group]
        )
        self.user2 = hydroshare.create_account(
            'test_user2@email.com',
            username='owner2',
            first_name='owner2_first_name',
            last_name='owner2_last_name',
            superuser=False,
            groups=[self.hs_group]
        )

        self.res = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.user1,
            title='My Test Resource'
        )
        # test to make sure one owner can transfer quota holder to another owner
        self.user1.uaccess.share_resource_with_user(self.res, self.user2, PrivilegeCodes.OWNER)

    def test_change_quota_holder(self):
        # here we are testing the change_quota_holder view function
        url_params = {'shortkey': self.res.short_id}
        url = reverse('change_quota_holder', kwargs=url_params)
        request = self.factory.post(url, data={'new_holder_username': 'owner2'})
        request.user = self.user1

        self.add_session_to_request(request)
        response = change_quota_holder(request, shortkey=self.res.short_id)
        response_data = json.loads(response.content)
        self.assertTrue(self.res.get_quota_holder() == self.user2)
        self.assertEqual(response_data['status'], 'success')

        # clean up
        hydroshare.delete_resource(self.res.short_id)
