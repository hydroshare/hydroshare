__author__ = 'Tian Gan'

## unit test for get_user_info() from users.py

## Notes:
# According to the API requirement. The User ID is used to get the user info such as profile and group

# The current get_user_info() can get the user info using the user instance but can't get the user info using the User ID

# The obtained user info includes the following without group info.
# {u'username': u'user1', u'first_name': u'user1_first', u'last_name': u'user1_last', u'email': u'user1@gmail.com',
#  u'last_login': u'2014-05-28T21:58:31.324975', u'resource_uri': u'/api/v1/user/1/', u'id': 1,
#  u'date_joined': u'2014-05-28T21:58:31.324975'}

from django.test import TestCase
from django.contrib.auth.models import User, Group
from hs_core import hydroshare


class TestGetUserInfo(TestCase):
    def setUp(self):

        # create a group
        self.group = hydroshare.create_group(
            'Test group',
            members=[],
            owners=[]
        )

        # create a user
        self.user = hydroshare.create_account(
            'user1@gmail.com',
            username='user1',
            first_name='user1_first',
            last_name='user1_last',
            superuser=False,
            groups=[self.group]
        )

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()

    def test_get_user_info_by_obj(self):
        user_info = hydroshare.get_user_info(self.user)
        # print serializers.serialize('json', User.objects.all())

        # test user username
        self.assertEqual(
            user_info['username'],
            self.user.username,
            msg='user username is not correct'
        )

        # test user email
        self.assertEqual(
            user_info['email'],
            self.user.email,
            msg='user email is not correct'
        )

        # test user name
        self.assertEqual(
            user_info['last_name'],
            self.user.last_name,
            msg='user last name is not correct'
        )

        self.assertEqual(
            user_info['first_name'],
            self.user.first_name,
            msg='user first name is not correct'
        )

        # # test user group info
        # self.assertEqual(
        #     user_info['groups'],
        #     [self.group.name],
        #     msg='user group info is not correct'
        # )

    def test_get_user_info_by_pk(self):
        try:
            user_info = hydroshare.get_user_info(self.user.pk)
        except:
            raise ValueError("get user info using user pk doesn't work.")
        else:
            # test user username
            self.assertEqual(
                user_info['username'],
                self.user.username,
                msg='obtained username is not correct'
            )

            # test user email
            self.assertEqual(
                user_info['email'],
                self.user.email,
                msg='obtained email is not correct'
            )

            # test user name
            self.assertEqual(
                user_info['last_name'],
                self.user.last_name,
                msg='user last name is not correct'
            )

            self.assertEqual(
                user_info['first_name'],
                self.user.first_name,
                msg='user first name is not correct'
            )

            # # test user group info
            # self.assertEqual(
            #     user_info['groups'],
            #     self.group.name,
            #     msg='obtained groups info is not correct'
            # )

