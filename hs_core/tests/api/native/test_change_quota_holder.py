import uuid
from unittest import TestCase

from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.test import TestCase as DjangoTestCase

from hs_core.hydroshare import resource
from hs_core.testing import MockS3TestCaseMixin
from hs_core import hydroshare
from hs_access_control.models import PrivilegeCodes
from hs_core.hydroshare.utils import QuotaException


class TestChangeQuotaHolder(MockS3TestCaseMixin, TestCase):
    def setUp(self):
        super(TestChangeQuotaHolder, self).setUp()

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create two users
        self.user1 = hydroshare.create_account(
            'test_user1@email.com',
            username='owner1' + uuid.uuid4().hex,
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
        # create files
        n1 = "test1.txt"
        test_file = open(n1, 'w')
        test_file.write("Test text file in test1.txt")
        test_file.close()
        # open files for read and upload
        myfile1 = open(n1, "rb")

        res = resource.create_resource(
            'CompositeResource',
            self.user1,
            'My Test Resource',
            files=[myfile1],
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

        uquota.save_allocated_value(1, "B")

        # QuotaException should be raised when attempting to change quota holder to user1 when
        # quota is enforced
        with self.assertRaises(QuotaException):
            res.set_quota_holder(self.user2, self.user1)

        uquota.save_allocated_value(20, "GB")

        # QuotaException should NOT be raised now that more quota is allocated
        res.set_quota_holder(self.user2, self.user1)

        if res:
            res.delete()


class TestChangeQuotaHolderCommunityRestriction(MockS3TestCaseMixin, DjangoTestCase):
    def setUp(self):
        super(TestChangeQuotaHolderCommunityRestriction, self).setUp()

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        # owner1 will act as the resource creator/first owner
        self.owner1 = hydroshare.create_account(
            'owner1@email.com',
            username='owner1' + uuid.uuid4().hex,
            first_name='owner1_first_name',
            last_name='owner1_last_name',
            superuser=False,
            groups=[self.hs_group]
        )

        # restricted_user is the account whose UserQuota carries the community restriction
        self.restricted_user = hydroshare.create_account(
            'restricted_user@email.com',
            username='restricted_user' + uuid.uuid4().hex,
            first_name='restricted_first_name',
            last_name='restricted_last_name',
            superuser=False,
            groups=[self.hs_group]
        )

        # qualifying_owner belongs to a group that is a member of the required community
        self.qualifying_owner = hydroshare.create_account(
            'qualifying_owner@email.com',
            username='qualifying_owner' + uuid.uuid4().hex,
            first_name='qualifying_first_name',
            last_name='qualifying_last_name',
            superuser=False,
            groups=[self.hs_group]
        )

        # non_qualifying_owner does not belong to any group in the required community
        self.non_qualifying_owner = hydroshare.create_account(
            'non_qualifying_owner@email.com',
            username='non_qualifying_owner' + uuid.uuid4().hex,
            first_name='non_qualifying_first_name',
            last_name='non_qualifying_last_name',
            superuser=False,
            groups=[self.hs_group]
        )

        self.required_community = self.owner1.uaccess.create_community(
            'Required Community',
            'A community used to restrict quota holder changes.'
        )
        self.required_community.active = True
        self.required_community.save()

        self.qualifying_group = self.qualifying_owner.uaccess.create_group(
            title='Qualifying Group',
            description='Group that belongs to the required community.'
        )
        self.owner1.uaccess.share_community_with_group(
            self.required_community, self.qualifying_group, PrivilegeCodes.VIEW
        )

        # set the community restriction on restricted_user's UserQuota
        user_quota = self.restricted_user.quotas.get()
        user_quota.required_community_membership = self.required_community
        user_quota.save()

        self.res = resource.create_resource(
            'CompositeResource',
            self.owner1,
            'My Restricted Quota Holder Resource',
        )

    def tearDown(self):
        if self.res:
            self.res.delete()
        super(TestChangeQuotaHolderCommunityRestriction, self).tearDown()

    def test_denied_when_setter_does_not_qualify(self):
        # owner1 (setter) does not belong to any group in the required community
        self.owner1.uaccess.share_resource_with_user(
            self.res, self.restricted_user, PrivilegeCodes.OWNER
        )

        with self.assertRaises(PermissionDenied):
            self.res.set_quota_holder(self.owner1, self.restricted_user)

    def test_allowed_when_setter_qualifies(self):
        # qualifying_owner (setter) belongs to a group in the required community
        self.owner1.uaccess.share_resource_with_user(
            self.res, self.restricted_user, PrivilegeCodes.OWNER
        )
        self.owner1.uaccess.share_resource_with_user(
            self.res, self.qualifying_owner, PrivilegeCodes.OWNER
        )

        self.res.set_quota_holder(self.qualifying_owner, self.restricted_user)
        self.assertEqual(self.res.quota_holder, self.restricted_user)

    def test_new_holders_own_membership_does_not_satisfy_check_for_a_different_setter(self):
        # even if restricted_user (the new holder) is themselves a member of the qualifying
        # group, this should not satisfy the check when a different, non-qualifying user (owner1)
        # is the one making the change
        self.qualifying_owner.uaccess.share_group_with_user(
            self.qualifying_group, self.restricted_user, PrivilegeCodes.VIEW
        )
        self.owner1.uaccess.share_resource_with_user(
            self.res, self.restricted_user, PrivilegeCodes.OWNER
        )

        with self.assertRaises(PermissionDenied):
            self.res.set_quota_holder(self.owner1, self.restricted_user)

    def test_allowed_when_restricted_user_is_setter_and_qualifies(self):
        # when restricted_user is both the setter and the new holder, their own membership in a
        # qualifying group is sufficient to satisfy the check
        self.qualifying_owner.uaccess.share_group_with_user(
            self.qualifying_group, self.restricted_user, PrivilegeCodes.VIEW
        )
        self.owner1.uaccess.share_resource_with_user(
            self.res, self.restricted_user, PrivilegeCodes.OWNER
        )

        self.res.set_quota_holder(self.restricted_user, self.restricted_user)
        self.assertEqual(self.res.quota_holder, self.restricted_user)

    def test_unaffected_when_no_restriction_set(self):
        # sanity check: users without a community restriction on their UserQuota are unaffected
        self.owner1.uaccess.share_resource_with_user(
            self.res, self.non_qualifying_owner, PrivilegeCodes.OWNER
        )

        self.res.set_quota_holder(self.owner1, self.non_qualifying_owner)
        self.assertEqual(self.res.quota_holder, self.non_qualifying_owner)
