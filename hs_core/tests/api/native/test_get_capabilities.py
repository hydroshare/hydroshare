"""
Unittest for def get_capabilities(pk)

author's notes-
I think this should be renamed get_extra_capabilities
must be extended to test other types of resources

"""

from django.contrib.auth.models import Group, User
from django.test import TestCase

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.testing import MockIRODSTestCaseMixin


class TestGetCapabilities(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestGetCapabilities, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

    def tearDown(self):
        super(TestGetCapabilities, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        self.res.delete()
        BaseResource.objects.all().delete()

    def test_generic(self):
        user = hydroshare.create_account(email='shauntheta@gmail.com', username='shaun', first_name='shaun',
                                         last_name='livingston', superuser=False, groups=[self.group])
        self.res = hydroshare.create_resource('CompositeResource', user, 'Test Resource')

        # this is the api call we are testing
        extras = hydroshare.get_capabilities(self.res.short_id)
        self.assertIsNone(extras)
