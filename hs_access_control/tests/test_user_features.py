from django.test import TestCase
from django.contrib.auth.models import Group

from hs_access_control.models import FeatureCodes

from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin

from hs_access_control.tests.utilities import global_reset


class UserFeatures(MockS3TestCaseMixin, TestCase):

    def setUp(self):
        super(UserFeatures, self).setUp()

        global_reset()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='administrator',
            last_name='couch',
            superuser=True,
            groups=[]
        )

        self.cat = hydroshare.create_account(
            'cat@gmail.com',
            username='cat',
            first_name='not a dog',
            last_name='last_name_cat',
            superuser=False,
            groups=[]
        )

    def test_01_no_feature(self):
        """With no features, no features are enabled"""
        cat = self.cat
        self.assertFalse(cat.uaccess.feature_enabled(FeatureCodes.CZO))

    def test_02_CZO_enable(self):
        """Enable CZO feature"""
        cat = self.cat
        self.assertFalse(cat.uaccess.feature_enabled(FeatureCodes.CZO))
        cat.uaccess.customize(FeatureCodes.CZO, True)
        self.assertTrue(cat.uaccess.feature_enabled(FeatureCodes.CZO))
        cat.uaccess.customize(FeatureCodes.CZO, False)
        self.assertFalse(cat.uaccess.feature_enabled(FeatureCodes.CZO))
        cat.uaccess.customize(FeatureCodes.CZO, True)
        self.assertTrue(cat.uaccess.feature_enabled(FeatureCodes.CZO))
        cat.uaccess.uncustomize(FeatureCodes.CZO)
        self.assertFalse(cat.uaccess.feature_enabled(FeatureCodes.CZO))
