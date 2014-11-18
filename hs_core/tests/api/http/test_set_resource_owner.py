__author__ = 'shaunjl'
"""
Tastypie REST API tests for SetResourceOwner.as_view

comments- set owner test gives 403

"""
from django.contrib.auth.models import User
from hs_core import hydroshare
from tastypie.test import ResourceTestCase, TestApiClient
from tastypie.serializers import Serializer
from hs_core.models import GenericResource

class SetResourceOwnerTest(ResourceTestCase):
    serializer = Serializer()
    def setUp(self):
        self.api_client=TestApiClient()

        self.user = hydroshare.create_account(
            'shaun@gmail.com',
            username='user',
            first_name='User_FirstName',
            last_name='User_LastName',
            password='foobar',
            superuser=True
        )
        self.url_base = '/hsapi/resource/owner/'
        self.api_client.client.login(username=self.user.username, password=self.user.password)

    def tearDown(self):
        User.objects.all().delete()

    def test_set_owner(self):
        res = hydroshare.create_resource('GenericResource', self.user, 'res1')
        user2 = hydroshare.create_account(
            'shaun@gmail.com',
            username='user2',
            first_name='User2_FirstName',
            last_name='User2_LastName',
            password='password'
        )
        post_data={ 'user': user2.pk, 'api_key' : self.user.api_key.key }
        url='{0}{1}/'.format(self.url_base,res.short_id)
        resp = self.api_client.put(url, data=post_data)

        self.assertEqual(resp.body, res.short_id)


        hydroshare.delete_resource(res.short_id)
