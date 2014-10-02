__author__ = 'shaunjl'
"""
Tastypie API tests for update_account

comments-  IMPORTANT- update_account(user, **kwargs) contains a 'blacklist,' that chucks
the username,password, and groups, if given. I only fixed it to work, but kept the blacklist
as a relic to hopefully jog the developers memory as to what he intended there.
"""
from tastypie.test import ResourceTestCase, TestApiClient
from tastypie.serializers import Serializer
from django.contrib.auth.models import User, Group
from hs_core import hydroshare

class UpdateAccountTest(ResourceTestCase):
    def setUp(self):
        self.user = hydroshare.create_account(
            'shaun@gmail.com',
            username='shaunjl',
            first_name='shaun',
            last_name='john',
            superuser=True,
            )
    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()

    def test_basic(self):
        kwargs = {'groups': ('group0'),
                  'email': 'shauntheta@gmail.com',
                  'username': 'shaunuser',
                  'first_name': 'john',
                  'last_name': 'livingston',
                  'notes': 'these are some notes'}

        hydroshare.update_account(self.user, **kwargs)

        self.assertEqual(self.user.email, 'shauntheta@gmail.com')
        self.assertEqual(self.user.first_name, 'john')
        self.assertEqual(self.user.last_name, 'livingston')
        self.assertEqual(self.user.get_profile().notes, 'these are some notes')
        self.assertTrue(Group.objects.filter(user=self.user).exists)

