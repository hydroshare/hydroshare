__author__ = 'Tian Gan'

## unit test for publish_resource() from resource.py

## Note:
# It can't test if the edit_groups are empty now,
# as the edit_group can't be assigned any value when creating a resource

import unittest

from django.contrib.auth.models import User, Group

from hs_core import hydroshare
from hs_core.models import GenericResource
from hs_core.testing import MockIRODSTestCaseMixin

class TestPublishResource(MockIRODSTestCaseMixin, unittest.TestCase):
    def setUp(self):
        super(TestPublishResource, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        # create a resource
        self.res = hydroshare.create_resource(
            'GenericResource',
            self.user,
            'Test Resource'
        )

    def tearDown(self):
        super(TestPublishResource, self).tearDown()
        self.user.uaccess.delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        GenericResource.objects.all().delete()

    def test_publish_resource(self):
        # publish resource
        hydroshare.publish_resource(self.res.short_id)
        self.pub_res = hydroshare.get_resource_by_shortkey(self.res.short_id)

        # test publish state
        self.assertTrue(
            self.pub_res.raccess.published,
            msg='The resoruce is not published'
        )

        # test frozen state
        self.assertTrue(
            self.pub_res.raccess.immutable,
            msg='The resource is not frozen'
        )

        # test if doi is assigned
        self.assertIsNotNone(
            self.pub_res.doi,
            msg='No doi is assigned with the published resource.'
        )

