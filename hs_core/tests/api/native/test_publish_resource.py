__author__ = 'Tian Gan'

import unittest

from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin


class TestPublishResource(MockIRODSTestCaseMixin, TestCase):
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

    # TODO: This test needs to be enabled once the publish_resource() function is updated to register resource DOI
    # with crossref. At that point the call to crossref needs to be mocked here in this test (IMPORTANT)
    @unittest.skip
    def test_publish_resource(self):
        # check status prior to publishing the resource
        self.assertFalse(
            self.res.raccess.published,
            msg='The resource is published'
        )

        self.assertFalse(
            self.res.raccess.immutable,
            msg='The resource is frozen'
        )

        self.assertIsNone(
            self.res.doi,
            msg='doi is assigned'
        )

        # there should not be published date type metadata element
        self.assertFalse(self.res.metadata.dates.filter(type='published').exists())

        # publish resource - this is the api we are testing
        hydroshare.publish_resource(self.res.short_id)
        self.pub_res = hydroshare.get_resource_by_shortkey(self.res.short_id)

        # test publish state
        self.assertTrue(
            self.pub_res.raccess.published,
            msg='The resource is not published'
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

        # there should now published date type metadata element
        self.assertTrue(self.pub_res.metadata.dates.filter(type='published').exists())
