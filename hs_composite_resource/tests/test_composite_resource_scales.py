# coding=utf-8
from django.contrib.auth.models import Group
from django.test import TransactionTestCase, Client
from django.urls import reverse
from django.db import reset_queries, connection

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_file_types.tests.utils import CompositeResourceTestMixin


class CompositeResourceScalesTest(
    MockIRODSTestCaseMixin, TransactionTestCase, CompositeResourceTestMixin
):
    def setUp(self):
        super(CompositeResourceScalesTest, self).setUp()
        self.client = Client()
        self.group, _ = Group.objects.get_or_create(name="Hydroshare Author")
        self.user = hydroshare.create_account(
            "user1@nowhere.com",
            username="user1",
            password='mypassword1',
            first_name="Creator_FirstName",
            last_name="Creator_LastName",
            superuser=False,
            groups=[self.group],
        )

        self.res_title = "Testing Composite Resource Scales"

    def tearDown(self):
        super(CompositeResourceScalesTest, self).tearDown()
        if self.composite_resource:
            self.composite_resource.delete()

    def test_composite_resource_my_resources_scales(self):
        # test that db queries for "my_resources" remain constant when adding more resources

        # there should not be any resource at this point
        self.assertEqual(BaseResource.objects.count(), 0)
        self.create_composite_resource()

        with self.assertNumQueries(8):
            response = self.client.get(reverse("my_resources"), follow=True)
            self.assertTrue(response.status_code == 200)

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")

        self.create_composite_resource()

        with self.assertNumQueries(7):
            response = self.client.get(reverse("my_resources"), follow=True)
            self.assertTrue(response.status_code == 200)
        self.assertEqual(BaseResource.objects.count(), 2)

    def test_composite_resource_landing_scales(self):
        # test that db queries for landing page have constant time complexity

        # user 1 login
        self.client.login(username='user1', password='mypassword1')

        # there should not be any resource at this point
        self.assertEqual(BaseResource.objects.count(), 0)
        self.create_composite_resource()

        reset_queries()
        response = self.client.get(f'/resource/{self.composite_resource.short_id}', follow=True)
        self.assertTrue(response.status_code == 200)
        one_queries = len(connection.queries)

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")
        self.create_composite_resource()

        reset_queries()
        response = self.client.get(f'/resource/{self.composite_resource.short_id}', follow=True)
        self.assertTrue(response.status_code == 200)
        two_queries = len(connection.queries)

        self.assertLessEqual(two_queries, one_queries)
