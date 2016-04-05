__author__ = 'shaunjl'
"""
tests for update_account() api

comments-  IMPORTANT- update_account(user, **kwargs) contains a 'blacklist,' that chucks
the username,password, and groups, if given. I only fixed it to work, but kept the blacklist
as a relic to hopefully jog the developers memory as to what he intended there.
"""
import os
import unittest

from django.contrib.auth.models import User, Group
from hs_core import hydroshare


class UpdateAccountTest(unittest.TestCase):
    def setUp(self):
        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'shaun@gmail.com',
            username='shaunjl',
            first_name='shaun',
            last_name='john',
            superuser=True,
            groups=[]
            )

        pic_file = "photo.tif"
        cv_file = "cv.pdf"
        self.pic_file = open(pic_file, "w")
        self.pic_file.close()
        self.cv_file = open(cv_file, "w")
        self.cv_file.close()

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        self.pic_file.close()
        os.remove(self.pic_file.name)
        self.cv_file.close()
        os.remove(self.cv_file.name)

    def test_account_update(self):
        # before update
        self.assertEqual(self.user.email, 'shaun@gmail.com')
        self.assertEqual(self.user.first_name, 'shaun')
        self.assertEqual(self.user.last_name, 'john')
        self.assertEqual(self.user.username, 'shaunjl')

        kwargs = {'email': 'shauntheta@gmail.com',
                  'username': 'shaunuser',
                  'first_name': 'john',
                  'last_name': 'livingston',
                  }

        hydroshare.update_account(self.user, **kwargs)

        # after update
        self.assertEqual(self.user.email, 'shauntheta@gmail.com')
        self.assertEqual(self.user.first_name, 'john')
        self.assertEqual(self.user.last_name, 'livingston')
        # username should not get changed
        self.assertEqual(self.user.username, 'shaunjl')

    def test_profile_update(self):
        # test default profile data
        user_profile = hydroshare.utils.get_profile(self.user)
        self.assertEqual(user_profile.title, None)
        self.assertEqual(user_profile.middle_name, None)
        self.assertEqual(user_profile.user_type, 'Unspecified')
        self.assertEqual(user_profile.subject_areas, None)
        self.assertEqual(user_profile.organization, None)
        self.assertEqual(user_profile.phone_1, None)
        self.assertEqual(user_profile.phone_1_type, None)
        self.assertEqual(user_profile.phone_2, None)
        self.assertEqual(user_profile.phone_2_type, None)
        self.assertEqual(user_profile.details, None)
        self.assertEqual(user_profile.picture, None)
        self.assertEqual(user_profile.cv, None)
        self.assertEqual(user_profile.state, None)
        self.assertEqual(user_profile.country, None)
        self.assertTrue(user_profile.public)

        self.pic_file = open(self.pic_file.name, "w")
        self.pic_file.close()
        # open file for read to upload
        pic_file_obj = open(self.pic_file.name, "r")

        self.cv_file = open(self.cv_file.name, "w")
        self.cv_file.close()
        # open file for read to upload
        cv_file_obj = open(self.cv_file.name, "r")

        # add profile data
        profile_data = {'title': "Software Engineer",
                        'middle_name': 'Larson',
                        'user_type': 'Computer Programming',
                        'subject_areas': 'Python, Django, SQL',
                        'organization': 'Utah State University',
                        'phone_1': '435-678-0987',
                        'phone_1_type': 'Work',
                        'phone_2': '435-345-9099',
                        'phone_2_type': 'Home',
                        'details': 'Some details about me',
                        'country': 'USA',
                        'state': 'UT',
                        'public': False,
                        'picture': pic_file_obj,
                        'cv': cv_file_obj,
                        }

        hydroshare.update_account(self.user, **profile_data)
        user_profile = hydroshare.utils.get_profile(self.user)

        # test profile data
        self.assertEqual(user_profile.title, 'Software Engineer')
        self.assertEqual(user_profile.middle_name, 'Larson')
        self.assertEqual(user_profile.user_type, 'Computer Programming')
        self.assertEqual(user_profile.subject_areas, 'Python, Django, SQL')
        self.assertEqual(user_profile.organization, 'Utah State University')
        self.assertEqual(user_profile.phone_1, '435-678-0987')
        self.assertEqual(user_profile.phone_1_type, 'Work')
        self.assertEqual(user_profile.phone_2, '435-345-9099')
        self.assertEqual(user_profile.phone_2_type, 'Home')
        self.assertEqual(user_profile.details, 'Some details about me')
        self.assertEqual(user_profile.country, 'USA')
        self.assertEqual(user_profile.state, 'UT')
        self.assertNotEquals(user_profile.picture, None)
        self.assertNotEquals(user_profile.cv, None)
        self.assertFalse(user_profile.public)
