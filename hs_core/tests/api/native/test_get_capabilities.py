"""
Unittest for def get_capabilities(pk)

author's notes- 
I think this should be renamed get_extra_capabilities
must be extended to test other types of resources

"""

import unittest

from django.contrib.auth.models import User, Group

from hs_core import hydroshare
from hs_core.models import GenericResource
from hs_core.testing import MockIRODSTestCaseMixin


class TestGetCapabilities(MockIRODSTestCaseMixin, unittest.TestCase):
    def setUp(self):
        super(TestGetCapabilities, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

    def tearDown(self):
        super(TestGetCapabilities, self).tearDown()
        GenericResource.objects.all().delete()
        User.objects.filter(username='shaun').delete()
        Group.objects.all().delete()

    def test_generic(self):
        user = hydroshare.create_account(email='shauntheta@gmail.com', username='shaun', first_name='shaun',
                                         last_name='livingston', superuser=False, groups=[self.group])
        res1 = hydroshare.create_resource('GenericResource', user, 'Test Resource')

        # this is the api call we are testing
        extras = hydroshare.get_capabilities(res1.short_id)
        self.assertIsNone(extras)
