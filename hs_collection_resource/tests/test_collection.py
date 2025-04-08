import json

from dateutil import parser
from django.contrib.auth.models import Group
from django.test import TransactionTestCase, Client
from django.db import reset_queries, connection

from hs_access_control.models import PrivilegeCodes
from hs_collection_resource.models import CollectionResource, CollectionDeletedResource
from hs_collection_resource.utils import update_collection_list_csv
from hs_collection_resource.views import _update_collection_coverages
from hs_core.hydroshare import create_resource, create_account, \
    create_empty_resource, create_new_version_resource, \
    update_science_metadata, copy_resource, delete_resource
from hs_core.hydroshare.resource import ResourceFile
from hs_core.testing import MockS3TestCaseMixin


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

        self.resGen3 = create_resource(
            resource_type='CompositeResource',
            owner=self.user1,
            title='Gen 3'
        )

        self.resGen4 = create_resource(
            resource_type='CompositeResource',
            owner=self.user1,
            title='Gen 4'
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

        self.resGen5 = create_resource(
            resource_type='CompositeResource',
            owner=self.user2,
            title='Gen 4'
        )

        base_url = "/hsapi/_internal/{0}"
        self.url_to_update_collection = base_url + "/update-collection/"
        self.url_to_collection_member_permission = base_url + "/collection-member-permission/{1}/"
        self.url_to_set_resource_flag = base_url + "/set-resource-flag/"
        self.url_to_delete_resource = base_url + "/delete-resource/DELETE/"
        self.url_to_update_collection_for_deleted_resources = \
            base_url + "/update-collection-for-deleted-resources/"
        self.url_to_calculate_collection_coverages = \
            "/hsapi/_internal/calculate-collection-coverages/{0}/"

    def test_collection_basic_functions(self):
        # test basic collection class with different res types

        self.assertEqual(self.resCollection.resources.count(), 0)
        # add res to collection.resources
        self.resCollection.resources.add(self.resGen1)

        # test count
        self.assertEqual(self.resCollection.resources.count(), 1)

        # test res in collection.resources
        self.assertIn(self.resGen1, self.resCollection.resources.all())

        # test collection in res.collections
        self.assertIn(self.resCollection, self.resGen1.collections.all())

        # test remove all res from collection.resources
        self.resCollection.resources.clear()
        self.assertEqual(self.resCollection.resources.count(), 0)

        # test collection NOT in res.collections
        self.assertNotIn(self.resCollection, self.resGen1.collections.all())

        # test adding same resources to multiple collection resources
        self.resCollection.resources.add(self.resGen1)
        self.resCollection_with_missing_metadata.resources.add(self.resGen1)

        # test resources are in both collection resource
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGen1, self.resCollection_with_missing_metadata.resources.all())

    def test_collection_deleted_resource(self):
        # test CollectionDeletedResource

        self.assertEqual(self.resCollection.deleted_resources.count(), 0)
        self.assertEqual(CollectionDeletedResource.objects.count(), 0)
        # create 2 CollectionDeletedResource obj and associate with collection
        CollectionDeletedResource.objects.create(resource_title=self.resGen1.metadata.title,
                                                 deleted_by=self.user1,
                                                 collection=self.resCollection)
        CollectionDeletedResource.objects.create(resource_title=self.resGen2.metadata.title,
                                                 deleted_by=self.user1,
                                                 collection=self.resCollection)

        self.assertEqual(CollectionDeletedResource.objects.count(), 2)
        self.assertEqual(self.resCollection.deleted_resources.count(), 2)
        self.assertEqual(self.resCollection.
                         deleted_resources.
                         filter(resource_title=self.resGen1.metadata.title).count(), 1)
        self.assertEqual(self.resCollection.
                         deleted_resources.
                         filter(resource_title=self.resGen2.metadata.title).count(), 1)

        # remove CollectionDeletedResource objs
        self.resCollection.deleted_resources.all().delete()
        self.assertEqual(CollectionDeletedResource.objects.count(), 0)
        self.assertEqual(self.resCollection.deleted_resources.count(), 0)

    def test_update_collection_set_add_remove_logic(self):
        # test update_type: set, add, remove

        self.assertEqual(self.resCollection.resources.count(), 0)
        url_to_update_collection = self.url_to_update_collection.format(self.resCollection.short_id)

        # user 1 login
        self.api_client.login(username='user1', password='mypassword1')

        # test "update_type=set"
        # add 3 private member resources :[resGen1 resGen2 resGen3]
        response = self.api_client.post(url_to_update_collection,
                                        {'update_type': 'set',
                                         'resource_id_list':
                                         [self.resGen1.short_id, self.resGen2.short_id,
                                          self.resGen3.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 3)
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGen2, self.resCollection.resources.all())
        self.assertIn(self.resGen3, self.resCollection.resources.all())

        # set new list: [resGen1 resGen3 resGen4]
        response = self.api_client.post(url_to_update_collection,
                                        {'update_type': 'set',
                                         'resource_id_list':
                                         [self.resGen1.short_id, self.resGen3.short_id,
                                          self.resGen4.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 3)
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGen3, self.resCollection.resources.all())
        self.assertIn(self.resGen4, self.resCollection.resources.all())
        # resGen2 should be gone
        self.assertNotIn(self.resGen2, self.resCollection.resources.all())

        # set empty list []
        response = self.api_client.post(url_to_update_collection,
                                        {'update_type': 'set',
                                         'resource_id_list':
                                         []}, )
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 0)

        # test "update_type=add"
        # add to list: [resGen1 resGen2 resGen3]
        response = self.api_client.post(url_to_update_collection,
                                        {'update_type': 'add',
                                         'resource_id_list':
                                         [self.resGen1.short_id, self.resGen2.short_id,
                                          self.resGen3.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 3)
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGen2, self.resCollection.resources.all())
        self.assertIn(self.resGen3, self.resCollection.resources.all())

        # add to list [resGen4]
        response = self.api_client.post(url_to_update_collection,
                                        {'update_type': 'add',
                                         'resource_id_list':
                                         [self.resGen4.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 4)
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGen2, self.resCollection.resources.all())
        self.assertIn(self.resGen3, self.resCollection.resources.all())
        self.assertIn(self.resGen4, self.resCollection.resources.all())

        # add to list: empty []
        response = self.api_client.post(url_to_update_collection,
                                        {'update_type': 'add',
                                         'resource_id_list':
                                         []}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 4)
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGen2, self.resCollection.resources.all())
        self.assertIn(self.resGen3, self.resCollection.resources.all())
        self.assertIn(self.resGen4, self.resCollection.resources.all())

        # add a resource that is already in collection -- error expected
        response = self.api_client.post(url_to_update_collection,
                                        {'update_type': 'add',
                                         'resource_id_list':
                                         [self.resGen3.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "error")
        self.assertEqual(self.resCollection.resources.count(), 4)
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGen2, self.resCollection.resources.all())
        self.assertIn(self.resGen3, self.resCollection.resources.all())
        self.assertIn(self.resGen4, self.resCollection.resources.all())

        # test "update_type=remove"
        # remove from collection: [resGen1 resGen3]
        response = self.api_client.post(url_to_update_collection,
                                        {'update_type': 'remove',
                                         'resource_id_list':
                                         [self.resGen1.short_id,
                                          self.resGen3.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 2)
        self.assertIn(self.resGen2, self.resCollection.resources.all())
        self.assertIn(self.resGen4, self.resCollection.resources.all())

        # remove from collection: empty []
        response = self.api_client.post(url_to_update_collection,
                                        {'update_type': 'remove',
                                         'resource_id_list':
                                         []}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 2)
        self.assertIn(self.resGen2, self.resCollection.resources.all())
        self.assertIn(self.resGen4, self.resCollection.resources.all())

        # remove a resource that is not in collection: [resGen1] -- error expected
        response = self.api_client.post(url_to_update_collection,
                                        {'update_type': 'remove',
                                         'resource_id_list':
                                         [self.resGen1.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "error")
        self.assertEqual(self.resCollection.resources.count(), 2)
        self.assertIn(self.resGen2, self.resCollection.resources.all())
        self.assertIn(self.resGen4, self.resCollection.resources.all())

        # remove all remain resources: [resGen2, resGen4]
        response = self.api_client.post(url_to_update_collection,
                                        {'update_type': 'remove',
                                         'resource_id_list':
                                         [self.resGen2.short_id,
                                          self.resGen4.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 0)

    def test_update_collection_own_permission(self):
        # test update_collection()

        self.assertEqual(self.resCollection.resources.count(), 0)
        self.assertFalse(self.resCollection.can_be_public_or_discoverable)
        url_to_update_collection = self.url_to_update_collection.format(self.resCollection.short_id)

        # anonymous user
        # should inform frontend error
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list':
                                         [self.resGen1.short_id, self.resGen2.short_id,
                                          self.resGen3.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "error")
        self.assertEqual(resp_json["metadata_status"], "Insufficient to make public")
        self.assertFalse(self.resCollection.can_be_public_or_discoverable)

        # user 1 login
        self.api_client.login(username='user1', password='mypassword1')

        # add 3 private member resources
        # should inform frontend "sufficient to make public"
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list':
                                         [self.resGen1.short_id, self.resGen2.short_id,
                                          self.resGen3.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["metadata_status"], "Sufficient to make public")
        self.assertTrue(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 3)
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGen2, self.resCollection.resources.all())
        self.assertIn(self.resGen3, self.resCollection.resources.all())

        # remove renGen2 (just add 1 and 3)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list':
                                         [self.resGen1.short_id, self.resGen3.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["metadata_status"], "Sufficient to make public")
        self.assertTrue(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 2)
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertNotIn(self.resGen2, self.resCollection.resources.all())
        self.assertIn(self.resGen3, self.resCollection.resources.all())

        # remove all existing contained resources
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': []},
                                        )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["metadata_status"], "Insufficient to make public")
        self.assertFalse(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 0)

        # add resGen1, resGen2, and resGen5 (no permission)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list':
                                         [self.resGen1.short_id, self.resGen2.short_id,
                                          self.resGen5.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "error")
        self.assertEqual(self.resCollection.resources.count(), 0)

        # add resGen1 and resGen3
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list':
                                         [self.resGen1.short_id, self.resGen3.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["metadata_status"], "Sufficient to make public")
        self.assertTrue(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 2)
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGen3, self.resCollection.resources.all())

        # remove resGen1 and resGen3, add resGen2 and resGen5 (no permission)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list':
                                         [self.resGen2.short_id, self.resGen5.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "error")
        self.assertEqual(self.resCollection.resources.count(), 2)
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGen3, self.resCollection.resources.all())

        # grants View permission to User 1 over resGen5
        self.user2.uaccess.share_resource_with_user(self.resGen5, self.user1, PrivilegeCodes.VIEW)

        # remove resGen1 and resGen3, add resGen2 and resGen5 (having permission)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list':
                                         [self.resGen2.short_id, self.resGen5.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertTrue(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 2)
        self.assertIn(self.resGen2, self.resCollection.resources.all())
        self.assertIn(self.resGen5, self.resCollection.resources.all())

        # make resGen5 not shareable
        self.resGen5.raccess.shareable = False
        self.resGen5.raccess.save()
        # remove all existing contained resources
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': []},
                                        )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 0)
        # trying to add resGen5 (for which user1 has vew permission) to the collection should fail as resGen5 is not
        # shareable
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen5.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "error")
        self.assertEqual(self.resCollection.resources.count(), 0)

        # make resGen5 not discoverable
        self.resGen5.raccess.discoverable = False
        self.resGen5.raccess.save()
        # remove all existing contained resources
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': []},
                                        )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 0)
        # trying to add resGen5 (for which user1 has vew permission) to the collection should fail as resGen5 is not
        # discoverable
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen5.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "error")
        self.assertEqual(self.resCollection.resources.count(), 0)

        # make resGen5 discoverable
        self.resGen5.raccess.discoverable = True
        self.resGen5.raccess.public = False
        self.resGen5.raccess.save()
        # trying to add resGen5 (resource discoverable but private) to the collection should be successful
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen5.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 1)

        # make resGen5 public
        self.resGen5.raccess.public = True
        self.resGen5.raccess.save()
        # trying to add resGen5 (public resource not shareable) to the collection should be successful
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen5.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 1)

        # test adding resources to a collection that does not have all the required metadata
        self.assertEqual(self.resCollection_with_missing_metadata.resources.count(), 0)
        url_to_update_collection = self.url_to_update_collection.format(
            self.resCollection_with_missing_metadata.short_id)

        self.assertFalse(self.resCollection_with_missing_metadata.can_be_public_or_discoverable)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list':
                                         [self.resGen1.short_id, self.resGen2.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertFalse(self.resCollection_with_missing_metadata.can_be_public_or_discoverable)

    def test_update_collection_edit_permission(self):
        self.assertEqual(self.resCollection.resources.count(), 0)
        url_to_update_collection = self.url_to_update_collection.format(self.resCollection.short_id)

        # User 2 login
        self.api_client.login(username='user2', password='mypassword2')

        # User 2: add resGen5 in to collection (User 2 has no permission over this collection)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen5.short_id]},
                                        )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "error")
        self.assertFalse(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 0)

        # grants View permission to User 2 over collection
        self.user1.uaccess.share_resource_with_user(self.resCollection,
                                                    self.user2, PrivilegeCodes.VIEW)

        # User 2: add resGen5 in to collection
        # (User 2 has View permission over this collection that is not enough)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen5.short_id]},
                                        )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "error")
        self.assertFalse(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 0)

        # grants Change permission to User 2 over collection
        self.user1.uaccess.share_resource_with_user(self.resCollection,
                                                    self.user2, PrivilegeCodes.CHANGE)

        # User 2: add resGen5 in to collection (User 2 has Change permission over this collection)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen5.short_id]},
                                        )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertTrue(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 1)
        self.assertIn(self.resGen5, self.resCollection.resources.all())

        # User 2: remove resGen5 and add resGen3 (no permission)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen3.short_id]},
                                        )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "error")
        self.assertTrue(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 1)
        self.assertIn(self.resGen5, self.resCollection.resources.all())

        # grants View permission to User 2 over renGen3
        self.user1.uaccess.share_resource_with_user(self.resGen3, self.user2, PrivilegeCodes.VIEW)

        # User 2: remove resGen5 and add resGen3 (View permission)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen3.short_id]},
                                        )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertTrue(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 1)
        self.assertIn(self.resGen3, self.resCollection.resources.all())

    def test_collection_holds_collection(self):
        # a collection resource can be added to another collection resource

        url_to_update_collection = self.url_to_update_collection.format(self.resCollection.short_id)

        # this collection should contain no resources at this point
        self.assertEqual(self.resCollection.resources.count(), 0)
        # user 1 login
        self.api_client.login(username='user1', password='mypassword1')

        # add collection to itself
        # json response status should be error
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resCollection.short_id]},
                                        )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "error")
        # collection still should have no resource
        self.assertEqual(self.resCollection.resources.count(), 0)

        # add one collection resource to another collection resource
        # json response status should be success
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list':
                                         [self.resCollection_with_missing_metadata.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        # collection should have 1 resource
        self.assertEqual(self.resCollection.resources.count(), 1)
        self.assertEqual(self.resCollection.resources.all()[0].resource_type.lower(),
                         "collectionresource")

    def test_update_collection_for_deleted_resources(self):
        self.assertEqual(self.resCollection.resources.count(), 0)
        self.assertEqual(self.resCollection.deleted_resources.count(), 0)
        self.assertFalse(self.resCollection.can_be_public_or_discoverable)

        # user 1 login
        self.api_client.login(username='user1', password='mypassword1')

        # add 2 resources into collection
        url_to_update_collection = self.url_to_update_collection.format(self.resCollection.short_id)

        self.api_client.post(url_to_update_collection,
                             {'resource_id_list': [self.resGen1.short_id, self.resGen2.short_id,
                                                   ]})
        self.assertEqual(self.resCollection.resources.count(), 2)
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGen2, self.resCollection.resources.all())
        self.assertTrue(self.resCollection.can_be_public_or_discoverable)

        # at this point there should be no tracked deleted resource for the collection
        self.assertEqual(self.resCollection.deleted_resources.count(), 0)

        # delete resGen1
        res_id_resGen1 = self.resGen1.short_id
        url_to_delete_resource_for_resGen1 = \
            self.url_to_delete_resource.format(self.resGen1.short_id)
        self.api_client.post(url_to_delete_resource_for_resGen1, HTTP_REFERER='http://foo/bar')

        # delete resGen2
        res_id_resGen2 = self.resGen2.short_id
        url_to_delete_resource_for_resGen2 = \
            self.url_to_delete_resource.format(self.resGen2.short_id)
        self.api_client.post(url_to_delete_resource_for_resGen2, HTTP_REFERER='http://foo/bar')

        # resGen1 and resGen2 should not be in collection.resources
        self.assertEqual(self.resCollection.resources.count(), 0)
        self.assertNotIn(self.resGen1, self.resCollection.resources.all())
        self.assertNotIn(self.resGen2, self.resCollection.resources.all())
        self.assertFalse(self.resCollection.can_be_public_or_discoverable)

        # deleted_resources has info about resGen1 and resGen2
        self.assertEqual(CollectionDeletedResource.objects.count(), 2)
        # there should be now 2 tracked deleted resources for the collection
        self.assertEqual(self.resCollection.deleted_resources.count(), 2)
        self.assertIn(CollectionDeletedResource.objects.get(resource_id=res_id_resGen1),
                      self.resCollection.deleted_resources.all())
        self.assertIn(CollectionDeletedResource.objects.get(resource_id=res_id_resGen2),
                      self.resCollection.deleted_resources.all())

        # test clear deleted_resources through view
        url_to_update_collection_for_deleted_resources = \
            self.url_to_update_collection_for_deleted_resources.format(
                self.resCollection.short_id)

        # log out User 1
        self.api_client.logout()
        # log in as User 2
        self.api_client.login(username='user2', password='mypassword2')

        # User 2 update_collection_for_deleted_resources --> error
        response = self.api_client.post(url_to_update_collection_for_deleted_resources)
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "error")
        self.assertEqual(self.resCollection.deleted_resources.count(), 2)

        # logout and login as User 1
        self.api_client.logout()
        self.api_client.login(username='user1', password='mypassword1')

        # User 1update_collection_for_deleted_resources --> success
        response = self.api_client.post(url_to_update_collection_for_deleted_resources)
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        # there should be now no tracked deleted resources for the collection
        self.assertEqual(self.resCollection.deleted_resources.count(), 0)
        self.assertEqual(CollectionDeletedResource.objects.count(), 0)

    def test_are_all_contained_resources_published(self):
        # no contained resource
        self.assertEqual(self.resCollection.resources.count(), 0)
        # should return False
        self.assertEqual(self.resCollection.are_all_contained_resources_published, False)

        self.assertEqual(self.resGen1.raccess.published, False)
        self.assertEqual(self.resGen2.raccess.published, False)

        # add 2 unpublished resources to collection
        self.resCollection.resources.add(self.resGen1)
        self.resCollection.resources.add(self.resGen2)
        self.assertEqual(self.resCollection.resources.count(), 2)
        # not all contained res are published
        self.assertEqual(self.resCollection.are_all_contained_resources_published, False)

        # manually set the first contained res (self.resGen1) to published
        self.resGen1.raccess.published = True
        self.resGen1.raccess.save()
        self.assertEqual(self.resGen1.raccess.published, True)
        # not all contained res are published
        self.assertEqual(self.resCollection.are_all_contained_resources_published, False)

        # manually set the second contained res (self.resGen2) to published as well
        self.resGen2.raccess.published = True
        self.resGen2.raccess.save()
        self.assertEqual(self.resGen1.raccess.published, True)
        self.assertEqual(self.resGen2.raccess.published, True)
        # all contained res are published now
        self.assertEqual(self.resCollection.are_all_contained_resources_published, True)

    def test_versioning(self):
        # no contained resource
        self.assertEqual(self.resCollection.resources.count(), 0)

        # add 3 resources to collection
        self.resCollection.resources.add(self.resGen1)
        self.resCollection.resources.add(self.resGen2)
        self.resCollection.resources.add(self.resCollection_with_missing_metadata)
        self.assertEqual(self.resCollection.resources.count(), 3)

        # make a new version of collection
        new_collection = create_empty_resource(self.resCollection.short_id, self.user1.username)

        new_collection = create_new_version_resource(self.resCollection, new_collection, self.user1)

        # test the new version is a collection
        self.assertTrue(isinstance(new_collection, CollectionResource))

        # new version collection should have same contained res as its original does
        self.assertEqual(new_collection.resources.count(), self.resCollection.resources.count())
        for contained_res in new_collection.resources.all():
            self.assertIn(contained_res, self.resCollection.resources.all())

        # changes to old version collection should not affect new version collection
        self.resCollection.resources.clear()
        self.assertEqual(self.resCollection.resources.count(), 0)
        self.assertEqual(new_collection.resources.count(), 3)

    def test_copy(self):
        # no contained resource
        self.assertEqual(self.resCollection.resources.count(), 0)

        # add 3 resources to collection
        self.resCollection.resources.add(self.resGen1)
        self.resCollection.resources.add(self.resGen2)
        self.resCollection.resources.add(self.resCollection_with_missing_metadata)
        self.assertEqual(self.resCollection.resources.count(), 3)

        # make a new copy of collection
        new_collection = create_empty_resource(self.resCollection.short_id, self.user1.username,
                                               action='copy')

        new_collection = copy_resource(self.resCollection, new_collection)

        # test the new copy is a collection
        self.assertTrue(isinstance(new_collection, CollectionResource))

        # new copy collection should have same contained res as its original does
        self.assertEqual(new_collection.resources.count(), self.resCollection.resources.count())
        for contained_res in new_collection.resources.all():
            self.assertIn(contained_res, self.resCollection.resources.all())

        # changes to old collection should not affect new copied collection
        self.resCollection.resources.clear()
        self.assertEqual(self.resCollection.resources.count(), 0)
        self.assertEqual(new_collection.resources.count(), 3)

    def test_update_collection_coverages(self):
        # collection has no coverages metadata by default
        self.assertEqual(self.resCollection.metadata.coverages.count(), 0)
        # add 2 resources without coverage metadata to collection
        self.resCollection.resources.add(self.resGen1)
        self.resCollection.resources.add(self.resGen2)
        self.assertEqual(self.resCollection.resources.count(), 2)
        # calculate overall coverages
        _update_collection_coverages(self.resCollection)
        # no collection coverage
        self.assertEqual(self.resCollection.metadata.coverages.count(), 0)
        # update resGen1 coverage
        metadata_dict = [{'coverage': {'type': 'period', 'value':
                         {'name': 'Name for period coverage',
                          'start': '1/1/2016', 'end': '12/31/2016'}}}, ]
        update_science_metadata(pk=self.resGen1.short_id, metadata=metadata_dict, user=self.user1)
        self.assertEqual(self.resGen1.metadata.coverages.count(), 1)
        # calculate overall coverages
        _update_collection_coverages(self.resCollection)
        # collection should have 1 coverage metadata: period
        self.assertEqual(self.resCollection.metadata.coverages.count(), 1)
        period_coverage_obj = self.resCollection.metadata.coverages.all()[0]
        self.assertEqual(period_coverage_obj.type.lower(), 'period')
        self.assertEqual(parser.parse(period_coverage_obj.value['start'].lower()),
                         parser.parse('1/1/2016'))
        self.assertEqual(parser.parse(period_coverage_obj.value['end'].lower()),
                         parser.parse('12/31/2016'))

        # update resGen2 coverage
        metadata_dict = [{'coverage': {'type': 'point', 'value':
                         {'name': 'Name for point coverage', 'east': '-20',
                          'north': '10', 'units': 'decimal deg'}}}, ]
        update_science_metadata(pk=self.resGen2.short_id, metadata=metadata_dict,
                                user=self.user1)
        self.assertEqual(self.resGen2.metadata.coverages.count(), 1)
        # calculate overall coverages
        _update_collection_coverages(self.resCollection)

        # collection should have 2 coverage metadata: period and point
        self.assertEqual(self.resCollection.metadata.coverages.count(), 2)
        # test period
        period_qs = self.resCollection.metadata.coverages.all().filter(type='period')
        self.assertEqual(period_qs.count(), 1)
        self.assertEqual(parser.parse(period_qs[0].value['start'].lower()),
                         parser.parse('1/1/2016'))
        self.assertEqual(parser.parse(period_qs[0].value['end'].lower()),
                         parser.parse('12/31/2016'))
        # test point
        point_qs = self.resCollection.metadata.coverages.all().filter(type='point')
        self.assertEqual(point_qs.count(), 1)
        self.assertEqual(point_qs[0].value['east'], -20)
        self.assertEqual(point_qs[0].value['north'], 10)

        # add a 3rd res with period and box coverages into collection
        metadata_dict = [{'coverage': {'type': 'period', 'value':
                         {'name': 'Name for period coverage',
                          'start': '1/1/2010', 'end': '6/1/2016'}}},
                         {'coverage': {'type': 'point', 'value':
                          {'name': 'Name for point coverage', 'east': '25',
                           'north': '-35', 'units': 'decimal deg'}}}]
        update_science_metadata(pk=self.resGen3.short_id, metadata=metadata_dict, user=self.user1)
        self.assertEqual(self.resGen3.metadata.coverages.count(), 2)
        self.resCollection.resources.add(self.resGen3)
        self.assertEqual(self.resCollection.resources.count(), 3)
        # calculate overall coverages
        _update_collection_coverages(self.resCollection)
        self.assertEqual(self.resCollection.metadata.coverages.count(), 2)
        # test period
        period_qs = self.resCollection.metadata.coverages.all().filter(type='period')
        self.assertEqual(period_qs.count(), 1)
        self.assertEqual(parser.parse(period_qs[0].value['start'].lower()),
                         parser.parse('1/1/2010'))
        self.assertEqual(parser.parse(period_qs[0].value['end'].lower()),
                         parser.parse('12/31/2016'))
        # test point
        point_qs = self.resCollection.metadata.coverages.all().filter(type='box')
        self.assertEqual(point_qs.count(), 1)
        self.assertEqual(point_qs[0].value['westlimit'], -20)
        self.assertEqual(point_qs[0].value['northlimit'], 10)
        self.assertEqual(point_qs[0].value['eastlimit'], 25)
        self.assertEqual(point_qs[0].value['southlimit'], -35)

        # test view func calculate_collection_coverages
        # user 1 login
        self.api_client.login(username='user1', password='mypassword1')
        # add 2 resources into collection
        url_to_calculate_collection_coverages = \
            self.url_to_calculate_collection_coverages.\
            format(self.resCollection.short_id)
        response = self.api_client.post(url_to_calculate_collection_coverages)
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(len(resp_json["new_coverage_list"]), 2)
        found_period = False
        found_box = False
        for cv in resp_json["new_coverage_list"]:
            if cv["type"] == 'period':
                found_period = True
                self.assertEqual(parser.parse(cv['value']['start'].lower()),
                                 parser.parse('1/1/2010'))
                self.assertEqual(parser.parse(cv['value']['end'].lower()),
                                 parser.parse('12/31/2016'))
                self.assertEqual(cv['element_id_str'], '-1')
            elif cv["type"] == 'box':
                found_box = True
                self.assertEqual(cv['value']['westlimit'], -20)
                self.assertEqual(cv['value']['northlimit'], 10)
                self.assertEqual(cv['value']['eastlimit'], 25)
                self.assertEqual(cv['value']['southlimit'], -35)
                self.assertEqual(cv['element_id_str'], '-1')
        self.assertTrue(found_period)
        self.assertTrue(found_box)

        # remove all contained res
        self.resCollection.resources.clear()
        _update_collection_coverages(self.resCollection)
        self.assertEqual(self.resCollection.metadata.coverages.count(), 0)

    def test_hasPart_metadata(self):

        # no contained res
        self.assertEqual(self.resCollection.resources.count(), 0)
        # no hasPart metadata
        self.assertEqual(self.resCollection.metadata.relations.count(), 0)

        url_to_update_collection = self.url_to_update_collection.format(self.resCollection.short_id)
        # user 1 login
        self.api_client.login(username='user1', password='mypassword1')
        # add 3 private member resources
        # should inform frontend "sufficient to make public"
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list':
                                         [self.resGen1.short_id, self.resGen2.short_id,
                                          self.resGen3.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 3)

        # should be 3 hasPart metadata
        self.assertEqual(self.resCollection.metadata.relations.count(), 3)

        # check contained res
        hasPart = "hasPart"

        # check self.resGen1.short_id
        value = self.resGen1.get_citation()
        self.assertEqual(
            self.resCollection.metadata.relations.filter(type=hasPart, value=value).count(), 1)
        # check self.resGen2.short_id
        value = self.resGen2.get_citation()
        self.assertEqual(
            self.resCollection.metadata.relations.filter(type=hasPart, value=value).count(), 1)
        # check self.resGen3.short_id
        value = self.resGen2.get_citation()
        self.assertEqual(
            self.resCollection.metadata.relations.filter(type=hasPart, value=value).count(), 1)

        # remove renGen2 (keep 1 and 3)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list':
                                         [self.resGen1.short_id, self.resGen3.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 2)

        # should be 2 hasPart metadata
        self.assertEqual(self.resCollection.metadata.relations.count(), 2)

        # check self.resGen1.short_id
        value = self.resGen1.get_citation()
        self.assertEqual(
            self.resCollection.metadata.relations.filter(type=hasPart, value=value).count(), 1)
        # check self.resGen2.short_id -- should be 0
        value = self.resGen2.get_citation()
        self.assertEqual(
            self.resCollection.metadata.relations.filter(type=hasPart, value=value).count(), 0)
        # check self.resGen3.short_id
        value = self.resGen3.get_citation()
        self.assertEqual(
            self.resCollection.metadata.relations.filter(type=hasPart, value=value).count(), 1)

    def test_save_resource_list_csv_to_bag(self):

        # test "update_text_file" attribute
        # by default it is 'True'
        self.assertEqual(self.resCollection.update_text_file, "True")
        # set it to 'False'
        self.resCollection.extra_data = {'update_text_file': 'False'}
        self.resCollection.save()
        self.assertEqual(self.resCollection.update_text_file, "False")
        # update_text_file is a read-only attribute
        with self.assertRaises(AttributeError):
            self.resCollection.update_text_file = "Invalid String"
        with self.assertRaises(AttributeError):
            self.resCollection.update_text_file = 1
        # set it back to 'True'
        self.resCollection.extra_data = {'update_text_file': 'True'}
        self.resCollection.save()
        self.assertEqual(self.resCollection.update_text_file, "True")

        # test update_collection_list_csv()
        self.assertEqual(self.resCollection.resources.count(), 0)
        self.resCollection.resources.add(self.resGen1)
        self.resCollection.resources.add(self.resGen2)
        self.resCollection.resources.add(self.resGen3)
        self.assertEqual(self.resCollection.resources.count(), 3)
        self.assertEqual(ResourceFile.objects.filter(object_id=self.resCollection.id).count(), 0)
        csv_list = update_collection_list_csv(self.resCollection)
        self.assertEqual(ResourceFile.objects.filter(object_id=self.resCollection.id).count(), 1)

        # csv_list should have 4 rows: header row + 3 data rows
        self.assertEqual(len(csv_list), 4)
        # add res_id to one list
        res_id_list = []
        res_id_list.append(csv_list[1][2])
        res_id_list.append(csv_list[2][2])
        res_id_list.append(csv_list[3][2])
        self.assertEqual(len(res_id_list), 3)
        self.assertIn(self.resGen1.short_id, res_id_list)
        self.assertIn(self.resGen2.short_id, res_id_list)
        self.assertIn(self.resGen3.short_id, res_id_list)

    def test_collection_resource_delete(self):
        """Here we are testing when a collection resource is deleted, the resources that were part of the
        collection resource won't have the 'isPartOf' relation metadata"""

        # no contained res in collection resource
        self.assertEqual(self.resCollection.resources.count(), 0)
        url_to_update_collection = self.url_to_update_collection.format(self.resCollection.short_id)
        # user 1 login
        self.api_client.login(username='user1', password='mypassword1')
        # add 2 private member resources to collection
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen1.short_id, self.resGen2.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 2)
        # check of the resources that are part of the collection resource has 'isPartOf' relation metadata
        self.assertEqual(self.resGen1.metadata.relations.filter(type='isPartOf').count(), 1)
        self.assertEqual(self.resGen2.metadata.relations.filter(type='isPartOf').count(), 1)
        # now delete the collection resource
        delete_resource(self.resCollection.short_id, request_username=self.user1)
        # check of the resources that were part of the deleted collection resource has no 'isPartOf' relation metadata
        self.assertEqual(self.resGen1.metadata.relations.filter(type='isPartOf').count(), 0)
        self.assertEqual(self.resGen2.metadata.relations.filter(type='isPartOf').count(), 0)

    def test_delete_resource_in_collection(self):
        """Here we are testing when a resource that is part of a collection resource is deleted, the collection
        resources won't have the 'hasPart' relation metadata for the deleted resource"""

        # no contained res in collection
        self.assertEqual(self.resCollection.resources.count(), 0)
        url_to_update_collection = self.url_to_update_collection.format(self.resCollection.short_id)
        # user 1 login
        self.api_client.login(username='user1', password='mypassword1')
        # add 2 private member resources to collection
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen1.short_id, self.resGen2.short_id]}, )
        resp_json = json.loads(response.content.decode())
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 2)
        # collection should have 2 hasPart relation metadata
        self.assertEqual(self.resCollection.metadata.relations.filter(type='hasPart').count(), 2)
        # check of the resources that are part of the collection resource has 'isPartOf' relation metadata
        self.assertEqual(self.resGen1.metadata.relations.filter(type='isPartOf').count(), 1)
        self.assertEqual(self.resGen2.metadata.relations.filter(type='isPartOf').count(), 1)
        # now delete resGen1
        delete_resource(self.resGen1.short_id, request_username=self.user1)
        self.assertEqual(self.resCollection.resources.count(), 1)
        # check of the resource that is still part of the collection resource has the isPartOf relation metadata
        self.assertEqual(self.resGen2.metadata.relations.filter(type='isPartOf').count(), 1)
        # collection should have 1 hasPart relation metadata
        self.assertEqual(self.resCollection.metadata.relations.filter(type='hasPart').count(), 1)

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
