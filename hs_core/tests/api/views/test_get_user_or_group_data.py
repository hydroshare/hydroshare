import json

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group, User
from django.core.urlresolvers import reverse
from django.http import Http404

from rest_framework import status

from hs_core import hydroshare
from hs_core.views import get_user_or_group_data


class TestGetUserData(TestCase):

    def setUp(self):
        super(TestGetUserData, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.username = 'john'
        self.password = 'jhmypassword'
        self.john = hydroshare.create_account(
            'john@gmail.com',
            username=self.username,
            first_name='John',
            last_name='Clarson',
            superuser=False,
            password=self.password,
            groups=[]
        )

        self.mike = hydroshare.create_account(
            'mike@gmail.com',
            username='mike',
            first_name='Mike',
            last_name='Jensen',
            superuser=False,
            groups=[]
        )

        self.factory = RequestFactory()

    def test_get_user_data(self):
        post_data = {'user_or_group_id': self.john.id, 'is_group': 'false'}
        url = reverse('get_user_or_group_data', kwargs=post_data)
        request = self.factory.post(url, data=post_data)
        request.user = self.mike
        response = get_user_or_group_data(request, user_or_group_id=self.john.id, is_group='false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['name'], 'Clarson, John')
        self.assertEqual(resp_json['email'], self.john.email)
        self.assertIn('/user/{}/'.format(self.john.id), resp_json['url'])
        self.assertEqual(resp_json['address'], '')
        self.assertEqual(resp_json['phone'], '')
        self.assertEqual(resp_json['organization'], '')
        self.assertEqual(resp_json['website'], '')

        # add some profile data for john

        # test middle name
        self.john.userprofile.middle_name = 'K'
        self.john.userprofile.save()
        response = get_user_or_group_data(request, user_or_group_id=self.john.id, is_group='false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['name'], 'Clarson, John K')
        self.assertEqual(resp_json['email'], self.john.email)
        self.assertIn('/user/{}/'.format(self.john.id), resp_json['url'])
        self.assertEqual(resp_json['address'], '')
        self.assertEqual(resp_json['phone'], '')
        self.assertEqual(resp_json['organization'], '')
        self.assertEqual(resp_json['website'], '')

        # test address
        self.john.userprofile.state = 'Utah'
        self.john.userprofile.save()
        response = get_user_or_group_data(request, user_or_group_id=self.john.id, is_group='false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['name'], 'Clarson, John K')
        self.assertEqual(resp_json['email'], self.john.email)
        self.assertIn('/user/{}/'.format(self.john.id), resp_json['url'])
        self.assertEqual(resp_json['address'], 'Utah')
        self.assertEqual(resp_json['phone'], '')
        self.assertEqual(resp_json['organization'], '')
        self.assertEqual(resp_json['website'], '')

        self.john.userprofile.state = ''
        self.john.userprofile.country = 'USA'
        self.john.userprofile.save()
        response = get_user_or_group_data(request, user_or_group_id=self.john.id, is_group='false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['name'], 'Clarson, John K')
        self.assertEqual(resp_json['email'], self.john.email)
        self.assertIn('/user/{}/'.format(self.john.id), resp_json['url'])
        self.assertEqual(resp_json['address'], 'USA')
        self.assertEqual(resp_json['phone'], '')
        self.assertEqual(resp_json['organization'], '')
        self.assertEqual(resp_json['website'], '')

        self.john.userprofile.state = 'Utah'
        self.john.userprofile.country = 'USA'
        self.john.userprofile.save()
        response = get_user_or_group_data(request, user_or_group_id=self.john.id, is_group='false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['name'], 'Clarson, John K')
        self.assertEqual(resp_json['email'], self.john.email)
        self.assertIn('/user/{}/'.format(self.john.id), resp_json['url'])
        self.assertEqual(resp_json['address'], 'Utah, USA')
        self.assertEqual(resp_json['phone'], '')
        self.assertEqual(resp_json['organization'], '')
        self.assertEqual(resp_json['website'], '')

        # test phone
        self.john.userprofile.phone_1 = '678-890-7890'
        self.john.userprofile.save()
        response = get_user_or_group_data(request, user_or_group_id=self.john.id, is_group='false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['name'], 'Clarson, John K')
        self.assertEqual(resp_json['email'], self.john.email)
        self.assertIn('/user/{}/'.format(self.john.id), resp_json['url'])
        self.assertEqual(resp_json['address'], 'Utah, USA')
        self.assertEqual(resp_json['phone'], '678-890-7890')
        self.assertEqual(resp_json['organization'], '')
        self.assertEqual(resp_json['website'], '')

        self.john.userprofile.phone_1 = ''
        self.john.userprofile.phone_2 = '555-333-9999'
        self.john.userprofile.save()
        response = get_user_or_group_data(request, user_or_group_id=self.john.id, is_group='false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['name'], 'Clarson, John K')
        self.assertEqual(resp_json['email'], self.john.email)
        self.assertIn('/user/{}/'.format(self.john.id), resp_json['url'])
        self.assertEqual(resp_json['address'], 'Utah, USA')
        self.assertEqual(resp_json['phone'], '555-333-9999')
        self.assertEqual(resp_json['organization'], '')
        self.assertEqual(resp_json['website'], '')

        self.john.userprofile.phone_1 = '678-890-7890'
        self.john.userprofile.phone_2 = '555-333-9999'
        self.john.userprofile.save()
        response = get_user_or_group_data(request, user_or_group_id=self.john.id, is_group='false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['name'], 'Clarson, John K')
        self.assertEqual(resp_json['email'], self.john.email)
        self.assertIn('/user/{}/'.format(self.john.id), resp_json['url'])
        self.assertEqual(resp_json['address'], 'Utah, USA')
        self.assertEqual(resp_json['phone'], '678-890-7890')
        self.assertEqual(resp_json['organization'], '')
        self.assertEqual(resp_json['website'], '')

        # test organization
        self.john.userprofile.organization = 'USU'
        self.john.userprofile.save()
        response = get_user_or_group_data(request, user_or_group_id=self.john.id, is_group='false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['name'], 'Clarson, John K')
        self.assertEqual(resp_json['email'], self.john.email)
        self.assertIn('/user/{}/'.format(self.john.id), resp_json['url'])
        self.assertEqual(resp_json['address'], 'Utah, USA')
        self.assertEqual(resp_json['phone'], '678-890-7890')
        self.assertEqual(resp_json['organization'], 'USU')
        self.assertEqual(resp_json['website'], '')

        # test website
        self.john.userprofile.website = 'www.usu.edu.org'
        self.john.userprofile.save()
        response = get_user_or_group_data(request, user_or_group_id=self.john.id, is_group='false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['name'], 'Clarson, John K')
        self.assertEqual(resp_json['email'], self.john.email)
        self.assertIn('/user/{}/'.format(self.john.id), resp_json['url'])
        self.assertEqual(resp_json['address'], 'Utah, USA')
        self.assertEqual(resp_json['phone'], '678-890-7890')
        self.assertEqual(resp_json['organization'], 'USU')
        self.assertEqual(resp_json['website'], 'www.usu.edu.org')

    def test_get_user_data_failure(self):
        # passing an id of a user that doesn't exist should raise exception
        non_existing_user_id = 9999999
        self.assertEqual(User.objects.filter(id=non_existing_user_id).first(), None)
        post_data = {'user_or_group_id': non_existing_user_id, 'is_group': 'false'}
        url = reverse('get_user_or_group_data', kwargs=post_data)
        request = self.factory.post(url, data=post_data)
        request.user = self.mike
        with self.assertRaises(Http404):
            get_user_or_group_data(request, user_or_group_id=non_existing_user_id, is_group='false')
