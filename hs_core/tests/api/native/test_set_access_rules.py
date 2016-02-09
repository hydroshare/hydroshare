__author__ = 'lisa_stillwell'

# TODO: This test for set_access_rules() api can be included in test run only after we fix the api.
# This api is currently not being used in the system. Cleanup this test at the time of hs_core api cleanup.

import unittest

from unittest import TestCase
from hs_core.hydroshare import resource
from hs_core.hydroshare import users
from hs_core.models import GenericResource
from django.contrib.auth.models import User
import datetime as dt


class TestSetAccessRules(TestCase):

    def setUp(self):
        # create an admin user
        self.admin_user = users.create_account(
            'adminuser@email.com',
            username='adminuser',
            first_name='Super',
            last_name='User',
            superuser=True,
            groups=[])

        # create a test user
        self.test_user = users.create_account(
            'testuser@email.com',
            username='testuser',
            first_name='Ima',
            last_name='Testuser',
            superuser=False,
            groups=[])

        self.new_res = resource.create_resource(
            'GenericResource',
            self.admin_user,
            'My Test Resource'
            )

        # get the user's id
        #self.userid = User.objects.get(username=self.user).pk

        self.test_group = users.create_group(
            'MyTestGroup',
            members=[self.admin_user],
            owners=[self.admin_user]
            )

    def tearDown(self):
        self.admin_user.delete()
        self.test_user.delete()
        self.test_group.delete()
        #self.new_res.delete()

    @unittest.skip
    def test_set_access_rules(self):

        res_id = self.new_res.short_id

        # test to see if everything is sane
        result = users.set_access_rules(res_id, user=None, group=None, access=users.PUBLIC, allow=True)
        self.assertEqual(
            res_id,
            result.short_id,
            msg="Incorrect or no resource id returned."
        )

        # make sure public access was set correctly
        self.assertTrue(
            self.new_res.public,
            msg="Access rule for PUBLIC = False, expected True"
        )

        self.new_res = users.set_access_rules(res_id, user=None, group=None, access=users.PUBLIC, allow=False)
        self.assertFalse(
            self.new_res.public,
            msg="Access rule for PUBLIC = True, expected False"
        )

        # make sure donotdistribute access was set correctly
        self.new_res = users.set_access_rules(res_id, user=None, group=None, access=users.DO_NOT_DISTRIBUTE, allow=True)
        self.assertEqual(
            self.new_res.do_not_distribute,
            True,
            msg="Access rule for DO_NOT_DISTRIBUTE = False, expected True"
        )


        self.new_res = users.set_access_rules(res_id, user=None, group=None, access=users.DO_NOT_DISTRIBUTE, allow=False)
        self.assertEqual(
            self.new_res.do_not_distribute,
            False,
            msg="Access rule for DO_NOT_DISTRIBUTE = True, expected False"
        )

        # test with fake resource id - expect an exception
#        self.assertRaises(
#            NotFound,
#            lambda: users.set_access_rules(121212, user=None, group=None, access=users.VIEW, allow=True)
#        )

        # test EDIT access with user id provided
        self.new_res = users.set_access_rules(res_id, user=self.test_user, group=None, access=users.EDIT, allow=True)
        self.assertTrue(
            self.new_res.edit_users.filter(pk=self.test_user.pk).exists(),
            msg="Failure when trying to add EDIT access for user"
        )

        self.new_res = users.set_access_rules(res_id, user=self.test_user, group=None, access=users.EDIT, allow=False)
        self.assertFalse(
            self.new_res.edit_users.filter(pk=self.test_user.pk).exists(),
            msg="Failure when trying to remove EDIT access for user"
        )

        # test EDIT access with no user id provided
        self.assertRaises(
            TypeError,
            lambda: users.set_access_rules(self.new_res, user=None, group=None, access=users.EDIT, allow=True)
        )

        # test VIEW access with group id provided
        self.new_res = users.set_access_rules(self.new_res, user=None, group=self.test_group, access=users.VIEW, allow=True)
        self.assertTrue(
            self.new_res.view_groups.filter(pk=self.test_group.pk).exists(),
            msg="Failure when trying to add VIEW access for group"
        )

        self.new_res = users.set_access_rules(self.new_res, user=None, group=self.test_group, access=users.VIEW, allow=False)
        self.assertFalse(
            self.new_res.view_groups.filter(pk=self.test_group.pk).exists(),
            msg="Failure when trying to remove VIEW access for group"
        )

        # test VIEW access with no group id provided
        self.assertRaises(
            TypeError,
            lambda: users.set_access_rules(self.new_res, user=None, group=None, access=users.VIEW, allow=True)
        )

        # test with fake access rule
        self.assertRaises(
            TypeError,
            lambda: users.set_access_rules(self.new_res, user=None, group=None, access="surprise_me", allow=True)
        )



