from unittest import TestCase

from django.contrib.auth.models import Group

from hs_core.hydroshare import resource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.hydroshare.utils import QuotaException
from django.conf import settings


class TestUpdateQuotaUsage(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestUpdateQuotaUsage, self).setUp()

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create two users
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username='test_user',
            first_name='test_user_first_name',
            last_name='test_user_last_name',
            superuser=False,
            groups=[self.hs_group]
        )

    def test_update_quota_usage(self):
        res = resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
            )

        self.assertTrue(res.creator == self.user)
        self.assertTrue(res.get_quota_holder() == self.user)
        attname = self.user.username + '-quota'
        ini_qsize = 2 # unit: GB
        istorage = res.get_irods_storage()
        istorage.setAVU(settings.IRODS_USERNAME, attname, ini_qsize, type='-u')
        get_qsize = istorage.getAVU(settings.IRODS_USERNAME, attname, type='-u')
        self.assertEqual(ini_qsize, int(get_qsize))

        uquota = self.user.quotas.first()
        # make user1's quota over hard limit 125%
        uquota.used_value = uquota.allocated_value * 1.3
        uquota.save()

        if res:
            res.delete()
