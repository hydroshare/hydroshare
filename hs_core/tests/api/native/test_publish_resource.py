__author__ = 'Tian Gan'

## unit test for publish_resource() from resource.py

## Note:
# It can't test if the edit_groups are empty now,
# as the edit_group can't be assigned any value when creating a resource

from django.test import TestCase
from django.contrib.auth.models import User, Group
from hs_core import hydroshare
from hs_core.models import GenericResource


class TestPublishResource(TestCase):
    def setUp(self):
        # create two users
        self.user1 = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        self.user2 = hydroshare.create_account(
            'creator2@usu.edu',
            username='creator2',
            first_name='Creator2_FirstName',
            last_name='Creator2_LastName',
            superuser=False,
            groups=[]
        )

        # create a group
        self.group = hydroshare.create_group(
            'Test group',
            members=[],
            owners=[self.user1]
        )

        # create a resource
        self.res = hydroshare.create_resource(
            'GenericResource',
            self.user1,
            'Test Resource',
            #edit_groups=[self.group],
            edit_users=[self.user1, self.user2]
        )

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        GenericResource.objects.all().delete()

    def test_publish_resource(self):
        # publish resource
        hydroshare.publish_resource(self.res.short_id)
        self.pub_res = hydroshare.get_resource_by_shortkey(self.res.short_id)

        # test publish state
        self.assertTrue(
            self.pub_res.published_and_frozen,
            msg='The resoruce is not published and frozen'
        )

        # test frozen state
        self.assertTrue(
            self.pub_res.frozen,
            msg='The resource is not frozen'
        )

        # test if resource has edit users
        self.assertListEqual(
            list(self.pub_res.edit_users.all()),
            [],
            msg='edit users list is not empty'
        )

        # test if resource has edit groups
        self.assertListEqual(
            list(self.pub_res.edit_groups.all()),
            [],
            msg='edit groups is not empty'
        )

        # test if doi is assigned
        self.assertIsNotNone(
            self.pub_res.doi,
            msg='No doi is assigned with the published resource.'
        )

