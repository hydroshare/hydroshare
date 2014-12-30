__author__ = 'shaunjl'
"""
Tastypie API tests for create_account

comments- not sure how to implement test_email_function

"""
from tastypie.test import ResourceTestCase, TestApiClient
from tastypie.serializers import Serializer
from django.contrib.auth.models import User, Group
from hs_core import hydroshare

class CreateAccountTest(ResourceTestCase):
    def setUp(self):
        pass
    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()

    def test_basic_superuser(self):
        username,first_name,last_name,password = 'shaunjl', 'shaun','joseph','mypass'
        user = hydroshare.create_account(
            'shaun@gmail.com',
            username=username,
            first_name=first_name,
            last_name=last_name,
            superuser=True,
            password=password,
            active=True
            )
        users_in_db=User.objects.all()
        db_user=users_in_db[0]
        self.assertEqual(user.username,db_user.username)
        self.assertEqual(user.first_name,db_user.first_name)
        self.assertEqual(user.last_name,db_user.last_name)
        self.assertEqual(user.password,db_user.password)
        self.assertEqual(user.is_superuser,db_user.is_superuser)
        self.assertEqual(user.is_active,db_user.is_active)

    def test_basic_user(self):
        username,first_name,last_name,password = 'shaunjl', 'shaun','joseph','mypass'
        user = hydroshare.create_account(
            'shaun@gmail.com',
            username=username,
            first_name=first_name,
            last_name=last_name,
            superuser=False,
            password=password,
            active=True
            )
        users_in_db=User.objects.all()
        db_user=users_in_db[0]
        self.assertEqual(user.username,db_user.username)
        self.assertEqual(user.first_name,db_user.first_name)
        self.assertEqual(user.last_name,db_user.last_name)
        self.assertEqual(user.password,db_user.password)
        self.assertEqual(user.is_superuser,db_user.is_superuser)
        self.assertEqual(user.is_active,db_user.is_active)

    def test_with_groups(self):
        g0 = hydroshare.create_group(name="group0")
        g1 = hydroshare.create_group(name="group1")
        g2 = hydroshare.create_group(name="group2")
        groups = [g0, g1, g2]

        username,first_name,last_name,password = 'shaunjl', 'shaun', 'joseph', 'mypass'
        user = hydroshare.create_account(
            'shaun@gmail.com',
            username=username,
            first_name=first_name,
            last_name=last_name,
            groups=groups
            )
        new_groups = list(Group.objects.filter(user=user.id))
        self.assertEqual(groups, new_groups)

    def test_email_function(self):
        pass





