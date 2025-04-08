import os
from django.test import TransactionTestCase, Client
from django.contrib.auth.models import Group

from hs_core.hydroshare import create_resource, create_account, UploadedFile
from hs_core.testing import MockS3TestCaseMixin

from hs_collection_resource.utils import get_collectable_resources


class TestCollection(MockS3TestCaseMixin, TransactionTestCase):

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

        self.res_1_user_1 = create_resource(
            resource_type='CompositeResource',
            owner=self.user1,
            title='Gen 1'
        )

        self.res_2_user_1 = create_resource(
            resource_type='CompositeResource',
            owner=self.user1,
            title='Gen 2'
        )

        self.user2 = create_account(
            'byu2@byu.edu',
            username='user2',
            password='mypassword2',
            first_name='myfirstname2',
            last_name='mylastname2',
            superuser=False,
            groups=[self.group]
        )

        test_file1 = open('test1.txt', 'w')
        test_file1.write("Test text file in test1.txt")
        test_file1.close()
        test_file1 = open('test1.txt', 'rb')
        files = [UploadedFile(file=test_file1, name='test1.txt')]
        metadata_dict = [{'description': {'abstract': 'My test abstract'}}]
        self.res_1_user_2 = create_resource(
            resource_type='CompositeResource',
            owner=self.user2,
            title='Gen 4',
            keywords=['kw1', 'kw2'],
            files=files,
            metadata=metadata_dict
        )

        self.res_2_user_2 = create_resource(
            resource_type='CompositeResource',
            owner=self.user2,
            title='Gen 3'
        )

    def tearDown(self):
        os.remove('test1.txt')

    def test_collectable_shareable_resources(self):
        # owned resources are collectable
        self.assertEqual(get_collectable_resources(self.user1, self.resCollection).all().count(), 2)
        # ensure resource not owned by user1 is public and shareable
        self.res_1_user_2.raccess.public = True
        self.res_1_user_2.raccess.shareable = True
        self.res_1_user_2.raccess.save()
        self.assertTrue(self.res_1_user_2.raccess.public)
        self.assertTrue(self.res_1_user_2.raccess.shareable)
        # claim user_2's resource for user_1
        self.user1.ulabels.claim_resource(self.res_1_user_2)
        # validate the claimed resource is included with the collectable result
        self.assertEqual(get_collectable_resources(self.user1, self.resCollection).all().count(), 3)
        # turning off sharing does not disallow sharing of public resources.
        self.res_1_user_2.raccess.shareable = False
        self.res_1_user_2.raccess.save()
        self.assertEqual(get_collectable_resources(self.user1, self.resCollection).all().count(), 2)

        # turn on discoverable to validate the claimed resource is included with the collectable result
        self.res_1_user_2.raccess.discoverable = True
        self.res_1_user_2.raccess.save()
        self.assertEqual(get_collectable_resources(self.user1, self.resCollection).all().count(), 3)
