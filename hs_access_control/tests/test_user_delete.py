
import unittest
from django.http import Http404
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group
from pprint import pprint

from hs_access_control.models import UserAccess, GroupAccess, ResourceAccess, \
    UserResourcePrivilege, GroupResourcePrivilege, UserGroupPrivilege, PrivilegeCodes

from hs_core import hydroshare
from hs_core.models import GenericResource, BaseResource
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.tests.utilities import *


class T12UserDelete(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(T12UserDelete, self).setUp()

        global_reset()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='administrator',
            last_name='couch',
            superuser=True,
            groups=[]
        )

        self.cat = hydroshare.create_account(
            'cat@gmail.com',
            username='cat',
            first_name='not a dog',
            last_name='last_name_cat',
            superuser=False,
            groups=[]
        )

        self.dog = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            first_name='a little arfer',
            last_name='last_name_dog',
            superuser=False,
            groups=[]
        )

        # self.scratching = hydroshare.create_resource(resource_type='GenericResource',
                                                     owner=self.cat,
                                                     title='all about sofas as scrathing posts',
                                                     metadata=[],)

        # self.felines = self.cat.uaccess.create_group(title='felines', description="We are the feliness")


    def test_00_delete(self):
        "Test that deleting a user cascade-deletes the uaccess record"
        # scratching = self.scratching
        # felines = self.felines
        # dog = self.dog
        cat = self.cat
        caccess = cat.uaccess

        # delete the user "cat" 
        cat.delete()
        
        # should not be able to get the now defunct "caccess" object. 
        self.assertEqual(list(UserAccess.objects.filter(id=caccess)), []) 



        

