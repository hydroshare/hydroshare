"""
Unittest for def get_capabilities(pk)

author's notes- 
I think this should be renamed get_extra_capabilities
must be extended to test other types of resources for release 3

"""

import unittest

from django.contrib.auth.models import User, Group

from hs_core import hydroshare
from hs_core.models import GenericResource
from hs_core.hydroshare.resource import create_resource, get_capabilities
from hs_core.testing import MockIRODSTestCaseMixin


class TestGetCapabilities(MockIRODSTestCaseMixin, unittest.TestCase):
    def setUp(self):
        super(TestGetCapabilities, self).setUp()

    def tearDown(self):
        GenericResource.objects.all().delete()
        User.objects.filter(username='shaun').delete()
        Group.objects.all().delete()
        super(TestGetCapabilities, self).tearDown()

    def test_generic(self):
        hydroshare_author_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        user = hydroshare.create_account(email='shauntheta@gmail.com', username='shaun', first_name='shaun',
                                         last_name='livingston', superuser=False, groups=[hydroshare_author_group])
        res1 = create_resource('GenericResource', user, 'res1')
        extras = get_capabilities(res1.short_id)
        self.assertIsNone(extras)
