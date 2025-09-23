from unittest import TestCase

from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from hs_core.hydroshare import resource
from hs_core.testing import MockS3TestCaseMixin
from hs_core import hydroshare
from hs_access_control.models import PrivilegeCodes


class TestSetDownloadAgreement(MockS3TestCaseMixin, TestCase):
    def setUp(self):
        super(TestSetDownloadAgreement, self).setUp()

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user_owner = hydroshare.create_account(
            'test_user_owner@email.com',
            username='mytestuserowner',
            first_name='some_first_name_owner',
            last_name='some_last_name_owner',
            superuser=False,
            groups=[self.hs_group]
        )
        self.user_non_owner = hydroshare.create_account(
            'test_user_non_owner@email.com',
            username='mytestusernonowner',
            first_name='some_first_name_non_owner',
            last_name='some_last_name_non_owner',
            superuser=False,
            groups=[self.hs_group]
        )

        self.res = resource.create_resource(
            'CompositeResource',
            self.user_owner,
            'My Test Resource'
        )

    def tearDown(self):
        super(TestSetDownloadAgreement, self).tearDown()
        self.res.delete()

    def test_set_download_agreement(self):
        """Here we are testing set_require_download_agreement() function of the resource object
        that only the owner can set the  require_download_agreement flag"""

        self.assertFalse(self.res.raccess.require_download_agreement)
        self.res.set_require_download_agreement(self.user_owner, value=True)
        self.assertTrue(self.res.raccess.require_download_agreement)
        # test that resource non owner can't set the flag
        with self.assertRaises(PermissionDenied):
            self.res.set_require_download_agreement(self.user_non_owner, value=True)

        # give user_non_owner resource view permission
        self.user_owner.uaccess.share_resource_with_user(self.res, self.user_non_owner,
                                                         PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied):
            self.res.set_require_download_agreement(self.user_non_owner, value=True)

        # give user_non_owner resource edit permission
        self.user_owner.uaccess.share_resource_with_user(self.res, self.user_non_owner,
                                                         PrivilegeCodes.CHANGE)
        with self.assertRaises(PermissionDenied):
            self.res.set_require_download_agreement(self.user_non_owner, value=True)

        # let the owner reset the flag
        self.res.set_require_download_agreement(self.user_owner, value=False)
        self.assertFalse(self.res.raccess.require_download_agreement)
