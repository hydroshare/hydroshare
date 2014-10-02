__author__ = 'shaunjl'
"""
Tastypie REST API tests for CreateOrListAccounts.as_view() modeled after: https://github.com/hydroshare/hs_core/blob/master/tests/api/http/test_resource.py

comments-
post returns TypeError, put returns HttpResponseForbidden (403)
get expects a json query in a dictionary like data={'query': self.serialize({'email': 'shaun@gmail.com})}

"""
from tastypie.test import ResourceTestCase, TestApiClient
from tastypie.serializers import Serializer
from django.contrib.auth.models import User 
from hs_core import hydroshare
from hs_core.views.users_api import CreateOrListAccounts

class CreateOrListAccountsTest(ResourceTestCase):
    serializer = Serializer()
    def setUp(self):
        self.account_url_base = '/hsapi/accounts/'
        self.sudo = hydroshare.create_account('info@hydroshare.org','hs','hydro','share',True,password='hs')

        self.api_client = TestApiClient()
        self.api_client.client.login(username=self.sudo.username, password=self.sudo.password)
        
    def tearDown(self):
        User.objects.all().delete()

    def test_create_account(self):
        username = 'creator'    
        password = 'password'
        
        post_data_should_fail = CreateOrListAccounts.CreateAccountForm({
            'email': 'shaun@gmail.com',
            'username': username,
            'first_name': 'shaun',
            'last_name': 'livingston',
            'password': password,
            'superuser': True           
        })

        resp=self.api_client.post(self.account_url_base, data=post_data_should_fail)
        self.assertHttpForbidden(resp)

        post_data_should_succeed = CreateOrListAccounts.CreateAccountForm({
            'email': 'shaun@gmail.com',
            'username': username,
            'first_name': 'shaun',
            'last_name': 'livingston',
            'password': password
        })
        resp=self.api_client.post(self.account_url_base, data=post_data_should_succeed)
        self.assertHttpCreated(resp)

        self.assertTrue(User.objects.filter(email='shaun@gmail.com').exists())
        self.assertTrue(User.objects.filter(username=username).exists())
        self.assertTrue(User.objects.filter(first_name='shaun').exists())
        self.assertTrue(User.objects.filter(last_name='livingston').exists())
        self.assertTrue(User.objects.filter(superuser=True).exists())

    def test_list_users(self):   

        hydroshare.create_account(
            'shaun@gmail.com',
            username='user0',
            first_name='User0_FirstName',
            last_name='User0_LastName',
        )

        hydroshare.create_account(
            'shaun@gmail.com',
            username='user1',
            first_name='User1_FirstName',
            last_name='User1_LastName',
        )

        hydroshare.create_account(
            'shaun@gmail.com',
            username='user2',
            first_name='User2_FirstName',
            last_name='User2_LastName',
        )

        num_of_accounts = len(User.objects.filter(email= 'shaun@gmail.com'))
        
        query = self.serialize({
            'email': 'shaun@gmail.com',
        })

        get_data = {'query': query}

        resp = self.api_client.get(self.account_url_base, data=get_data)
        
        self.assertEqual(resp.status_code,200)

        users = self.deserialize(resp) 

        self.assertTrue(len(users)==num_of_accounts)
        for num in range(num_of_accounts):
            self.assertEqual(str(users[num]['email']), 'shaun@gmail.com')
            self.assertEqual(str(users[num]['username']), 'user{0}'.format(num))
            self.assertEqual(str(users[num]['first_name']), 'User{0}_FirstName'.format(num))
            self.assertEqual(str(users[num]['last_name']), 'User{0}_LastName'.format(num))
            



'''
from list_users- 
print resp
Vary: Accept-Language, Cookie
Content-Type: application/json
Content-Language: en

[{"date_joined": "2014-05-20T20:05:13.755078", "email": "shaun@gmail.com", "first_name": "User0_FirstName",
  "id": 55, "last_login": "2014-05-20T20:05:13.755078", "last_name": "User0_LastName",
  "resource_uri": "/api/v1/user/55/", "username": "user0"}, {"date_joined": "2014-05-20T20:05:18.188848",
 "email": "shaun@gmail.com", "first_name": "User1_FirstName", "id": 56, "last_login": "2014-05-20T20:05:18.188848",
"last_name": "User1_LastName", "resource_uri": "/api/v1/user/56/", "username": "user1"},
 {"date_joined": "2014-05-20T20:05:21.802584", "email": "shaun@gmail.com", "first_name": "User2_FirstName",
  "id": 57, "last_login": "2014-05-20T20:05:21.802584", "last_name": "User2_LastName",
  "resource_uri": "/api/v1/user/57/", "username": "user2"}]

'''
