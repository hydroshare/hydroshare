import json

from django.contrib.auth.models import Group

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase

from hs_core.hydroshare import users


class TestUserInfo(APITestCase):

    def setUp(self):
        self.maxDiff = None
        self.client = APIClient()

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.email = 'test_user@email.com'
        self.username = 'testuser'
        self.first_name = 'some_first_name'
        self.last_name = 'some_last_name'

        self.user = users.create_account(
            self.email,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            superuser=False)

        self.client.force_authenticate(user=self.user)

    def test_user_info(self):
        response = self.client.get('/hsapi/userInfo/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['username'], self.username)
        self.assertEqual(content['email'], self.email)
        self.assertEqual(content['first_name'], self.first_name)
        self.assertEqual(content['last_name'], self.last_name)
