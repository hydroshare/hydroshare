import json

from django.contrib.auth.models import Group

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase

from hs_core.hydroshare import users, utils


class TestUserDetails(APITestCase):

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

        self.user.userprofile.phone_1 = '12345678'
        self.user.userprofile.state = 'Utah'
        self.user.userprofile.country = 'USA'
        self.user.userprofile.organization = 'CUAHSI'
        self.user.userprofile.website = 'https://www.hydroshare.org'
        self.user.userprofile.identifiers = {'ORCID': '1234566', 'ResearchGate': 'someresearchgateid'}
        self.user.userprofile.user_type = 'Computer Programming'
        self.user.userprofile.subject_areas = ['Hydrology', 'Water quality', 'Hydroinformatics']
        self.user.userprofile.save()

        self.client.force_authenticate(user=self.user)

    def _verify_user(self, response):
        user = self.user
        content = json.loads(response.content.decode())
        self.assertEqual(content['name'], utils.get_user_party_name(user))
        self.assertEqual(content['email'], self.email)
        self.assertEqual(content['url'], '{domain}/user/{uid}/'.format(domain=utils.current_site_url(), uid=user.pk))
        self.assertEqual(content['phone'], '12345678')
        self.assertEqual(content['address'], 'Utah, USA')
        self.assertEqual(content['organization'], 'CUAHSI')
        self.assertEqual(content['website'], 'https://www.hydroshare.org')
        self.assertEqual(content['identifiers']['ORCID'], '1234566')
        self.assertEqual(content['identifiers']['ResearchGate'], 'someresearchgateid')
        self.assertEqual(content['subject_areas'], ['Hydrology', 'Water quality', 'Hydroinformatics'])
        self.assertEqual(content['type'], 'Computer Programming')
        self.assertTrue(content['date_joined'])

    def test_user_details_username(self):
        response = self.client.get(f'/hsapi/userDetails/{self.username}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._verify_user(response)

    def test_user_details_userid(self):
        response = self.client.get(f'/hsapi/userDetails/{self.user.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._verify_user(response)

    def test_user_details_user_email(self):
        response = self.client.get(f'/hsapi/userDetails/{self.user.email}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._verify_user(response)

    def test_user_details_username_case_insensitive(self):
        response = self.client.get(f'/hsapi/userDetails/{self.username.upper()}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._verify_user(response)

    def test_user_details_user_email_case_insensitive(self):
        response = self.client.get(f'/hsapi/userDetails/{self.user.email.upper()}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self._verify_user(response)
