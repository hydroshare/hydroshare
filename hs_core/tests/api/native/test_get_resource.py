__author__ = 'tonycastronova'

from unittest import TestCase
from hs_core.hydroshare import resource
from hs_core.hydroshare import users
from hs_core.models import GenericResource, Bags
from django.contrib.auth.models import User
import datetime as dt


class TestGetResource(TestCase):

    def setUp(self):

        # create a user
        self.user = users.create_account(
            'test_user@email.com',
            username='sometestuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[])

        # get the user's id
        self.userid = User.objects.get(username=self.user).pk

        self.group = users.create_group(
            'MytestGroup',
            members=[self.user],
            owners=[self.user]
            )

        new_res = resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
            )
        self.pid = new_res.short_id

    def tearDown(self):
        self.user.delete()
        self.group.delete()
        #self.res.delete()

    def test_get_resource(self):

        # get the resource by pid
        res = resource.get_resource(self.pid).content_object

        self.assertTrue(res is not None)
        self.assertTrue(type(res) == GenericResource, type(res))
        self.assertTrue(res.title == 'My Test Resource')
        self.assertTrue(res.created.strftime('%m/%d/%Y %H:%M') == res.updated.strftime('%m/%d/%Y %H:%M') )
        self.assertTrue(res.created.strftime('%m/%d/%Y') == dt.datetime.today().strftime('%m/%d/%Y'))
        self.assertTrue(res.user == self.user)
        self.assertTrue(res.short_id is not None, 'Short ID has not been created!')




