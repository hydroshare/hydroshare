__author__ = 'Tian Gan'

## unit test http api GetResoruceList(View) from users_api.py


from tastypie.test import ResourceTestCase
from tastypie.test import TestApiClient
from tastypie.serializers import Serializer

from django.contrib.auth.models import User
from hs_core import hydroshare
from hs_core.models import GenericResource


class TestGetResourceList(ResourceTestCase):
    serializer = Serializer()

    def setUp(self):
        self.api_client = TestApiClient()
        self.username = 'jamy'
        self.password = '00001'

        # create a user
        self.user = hydroshare.create_account(
            'jamy@gmail.com',
            username=self.username,
            first_name='Tian',
            last_name='Gan',
            superuser=False,
            password=self.password,
            groups=[]
        )

        # create a resource
        self.res = hydroshare.create_resource(
            'GenericResource',
            self.user,
            'My resource'
        )

        # create a group
        self.group = hydroshare.create_group(
            'Test group',
            members=[],
            owners=[self.user1]
        )

    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()

    def test_get_resource_list(self):
        query = self.serialize({'user': self.username, 'keywords': ['a', 'b']})
        resp = self.api_client.get('/hsapi/resources/', data=query)
        self.assertEqual(resp.status_code, 200)





