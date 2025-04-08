from unittest import TestCase

from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from hs_core.hydroshare import resource
from hs_core.testing import MockS3TestCaseMixin
from hs_core import hydroshare
from hs_access_control.models import PrivilegeCodes
from hs_core.hydroshare.utils import QuotaException
from theme.models import QuotaMessage


class TestChangeQuotaHolder(MockS3TestCaseMixin, TestCase):
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

    def test_change_quota_holder(self):
        res = resource.create_resource(
            'CompositeResource',
            self.user1,
            'My Test Resource'
        )

        self.assertTrue(res.creator == self.user1)
        self.assertTrue(res.quota_holder == self.user1)
        self.assertFalse(res.raccess.public)
        self.assertFalse(res.raccess.discoverable)

        with self.assertRaises(PermissionDenied):
            res.set_quota_holder(self.user1, self.user2)

        # test to make sure one owner can transfer quota holder to another owner
        self.user1.uaccess.share_resource_with_user(res, self.user2, PrivilegeCodes.OWNER)
        res.set_quota_holder(self.user1, self.user2)
        self.assertTrue(res.quota_holder == self.user2)
        self.assertFalse(res.quota_holder == self.user1)

        # test to make sure quota holder cannot be removed from ownership
        with self.assertRaises(PermissionDenied):
            self.user1.uaccess.unshare_resource_with_user(res, self.user2)

        # test to make sure quota holder cannot be changed to an owner who is over-quota
        uquota = self.user1.quotas.first()
        # make user1's quota over hard limit 125%

        if not QuotaMessage.objects.exists():
            QuotaMessage.objects.create()
        qmsg = QuotaMessage.objects.first()
        qmsg.enforce_quota = True
        qmsg.save()

        from hs_core.tests.utils.test_utils import set_quota_usage_over_hard_limit
        set_quota_usage_over_hard_limit(uquota, qmsg)

        # QuotaException should be raised when attempting to change quota holder to user1 when
        # quota is enforced
        with self.assertRaises(QuotaException):
            res.set_quota_holder(self.user2, self.user1)

        qmsg.enforce_quota = False
        qmsg.save()

        # QuotaException should NOT be raised now that quota is not enforced
        res.set_quota_holder(self.user2, self.user1)

        if res:
            res.delete()
