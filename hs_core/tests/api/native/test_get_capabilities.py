'''
Unittest for def get_capabilities(pk)

author's notes- 
I think this should be renamed get_extra_capabilities
must be extended to test other types of resources for release 3

'''
__author__='shaunjl'

import unittest
from hs_core import hydroshare
from django.contrib.auth.models import User
from hs_core.models import GenericResource
from hs_core.hydroshare.resource import create_resource, get_capabilities

class TestGetCapabilities(unittest.TestCase):
    def setUp(self): #runs at the beginning of every test
        pass

    def tearDown(self): #runs at the end of every test
        GenericResource.objects.all().delete()
        User.objects.filter(username='shaun').delete()

    def test_generic(self):
        user = User.objects.create_user('shaun', 'shauntheta@gmail.com', 'shaun6745')
        res1 = create_resource('GenericResource', user, 'res1')
        extras = get_capabilities(res1.short_id)
        self.assertIsNone(extras)

    def test_othertypes(self):
         pass

