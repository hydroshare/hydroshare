from django.contrib.auth.models import Group
from django.test import TransactionTestCase, Client
from hs_core.hydroshare import create_resource, create_account
from hs_core.testing import MockIRODSTestCaseMixin
from django.db import reset_queries, connection


class TestCollection(MockIRODSTestCaseMixin, TransactionTestCase):

    def setUp(self):
        super(TestCollection, self).setUp()
        self.api_client = Client()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        self.user1 = create_account(
            'byu1@byu.edu',
            username='user1',
            password='mypassword1',
            first_name='myfirstname1',
            last_name='mylastname1',
            superuser=False,
            groups=[self.group]
        )

        self.resCollection = create_resource(
            resource_type='CollectionResource',
            owner=self.user1,
            title='My Collection',
            keywords=['kw1', 'kw2'],
            metadata=[{"rights": {"statement": "mystatement", "url": "http://www.google.com"}},
                      {"description": {"abstract": "myabstract"}}
                      ]
        )

        self.resCollection_with_missing_metadata = create_resource(
            resource_type='CollectionResource',
            owner=self.user1,
            title='My Collection with missing required metadata'
        )

        self.resGen1 = create_resource(
            resource_type='CompositeResource',
            owner=self.user1,
            title='Gen 1'
        )

        self.resGen2 = create_resource(
            resource_type='CompositeResource',
            owner=self.user1,
            title='Gen 2'
        )

    def test_collection_res_landing_scales(self):
        # test basic collection queries have constant time complexity

        # user 1 login
        self.api_client.login(username='user1', password='mypassword1')

        self.assertEqual(self.resCollection.resources.count(), 0)
        reset_queries()
        response = self.api_client.get(f'/resource/{self.resCollection.short_id}', follow=True)
        self.assertTrue(response.status_code == 200)

        # add res to collection.resources
        self.resCollection.resources.add(self.resGen1)

        # test count
        self.assertEqual(self.resCollection.resources.count(), 1)
        reset_queries()
        response = self.api_client.get(f'/resource/{self.resCollection.short_id}', follow=True)
        self.assertTrue(response.status_code == 200)
        single_queries = len(connection.queries)

        # add res to collection.resources
        self.resCollection.resources.add(self.resGen2)

        # test count
        self.assertEqual(self.resCollection.resources.count(), 2)
        reset_queries()
        response = self.api_client.get(f'/resource/{self.resCollection.short_id}', follow=True)
        self.assertTrue(response.status_code == 200)
        final_queries = len(connection.queries)

        self.assertLessEqual(final_queries, single_queries)
