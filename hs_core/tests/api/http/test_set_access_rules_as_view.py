__author__ = 'shaunjl'
"""
Tastypie REST API tests for SetAccessRules.as_view()

comments- getting 404s for both

"""
from tastypie.test import ResourceTestCase, TestApiClient
from tastypie.serializers import Serializer
from django.contrib.auth.models import User, Group 
from hs_core import hydroshare
from hs_core.views.users_api import SetAccessRules

class SetAccessRulesTest(ResourceTestCase):
    serializer = Serializer()
    def setUp(self):
        self.account_url_base = '/hsapi/resource/accessRules/'

        self.api_client = TestApiClient()
        
    def tearDown(self):
            User.objects.all().delete()
            Group.objects.all().delete()

    def test_set_user_rules(self):
        user = hydroshare.create_account(
            'shaun@gmail.com',
            username='user0',
            first_name='User0_FirstName',
            last_name='User0_LastName',
        )
        url = '{0}{1}/'.format(self.account_url_base, user.id)

        put_data = {
            'pid':user.id,
            'principaltype': 'user',
            'principleID': user.id,
            'access': 'view',
            'allow': 'true'
        }

        resp = self.api_client.put(url, data=put_data)

        self.assertEqual(resp.status_code, 200)

    def test_set_group_rules(self):   
        group = hydroshare.create_group(name="group0")

        url = '{0}{1}/'.format(self.account_url_base, group.id)

        put_data = self.serialize({
            'principaltype': 'group',
             'principleID': group.id,
             'access': 'view',
             'allow': 'true'
        })

        resp = self.api_client.put(url, data=put_data)

        self.assertEqual(resp.status_code, 200)
