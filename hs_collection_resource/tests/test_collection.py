import os
import shutil
import tempfile
import json

from django.test import TransactionTestCase, Client
from django.contrib.auth.models import Group

from hs_core.hydroshare import create_resource, create_account
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.models import PrivilegeCodes

from hs_collection_resource.models import CollectionDeletedResource


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
            resource_type='GenericResource',
            owner=self.user1,
            title='Gen 1'
        )

        self.resGen2 = create_resource(
            resource_type='GenericResource',
            owner=self.user1,
            title='Gen 2'
        )

        self.resGen3 = create_resource(
            resource_type='GenericResource',
            owner=self.user1,
            title='Gen 3'
        )

        self.resTimeSeries = create_resource(
            resource_type='TimeSeriesResource',
            owner=self.user1,
            title='Test Time Series Resource'
        )

        self.resNetCDF = create_resource(
                    resource_type='NetcdfResource',
                    owner=self.user1,
                    title='Test NetCDF Resource'
                )

        self.resGeoFeature = create_resource(
                    resource_type='GeographicFeatureResource',
                    owner=self.user1,
                    title='Test Geographic Feature (shapefiles)'
                )

        self.resModelInstance = create_resource(
                    resource_type='ModelInstanceResource',
                    owner=self.user1,
                    title='Test Model Instance Resource')

        self.user2 = create_account(
            'byu2@byu.edu',
            username='user2',
            password='mypassword2',
            first_name='myfirstname2',
            last_name='mylastname2',
            superuser=False,
            groups=[self.group]
        )

        self.resGen4 = create_resource(
            resource_type='GenericResource',
            owner=self.user2,
            title='Gen 4'
        )

        base_url = "/hsapi/_internal/{0}"
        self.url_to_update_collection = base_url + "/update-collection/"
        self.url_to_collection_member_permission = base_url + "/collection-member-permission/{1}/"
        self.url_to_set_resource_flag = base_url + "/set-resource-flag/"
        self.url_to_delete_resource = base_url + "/delete-resource/"
        self.url_to_update_collection_for_deleted_resources = base_url + "/update-collection-for-deleted-resources/"


    def test_collection_basic_functions(self):
        # test basic collection class with different res types

        self.assertEqual(self.resCollection.resources.count(), 0)
        # add res to collection.resources
        self.resCollection.resources.add(self.resGen1)
        self.resCollection.resources.add(self.resGeoFeature)
        self.resModelInstance.collections.add(self.resCollection)
        self.resTimeSeries.collections.add(self.resCollection)

        # test count
        self.assertEqual(self.resCollection.resources.count(), 4)

        # test res in collection.resources
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGeoFeature, self.resCollection.resources.all())
        self.assertIn(self.resModelInstance, self.resCollection.resources.all())
        self.assertIn(self.resTimeSeries, self.resCollection.resources.all())

        # test collection in res.collections
        self.assertIn(self.resCollection, self.resGen1.collections.all())
        self.assertIn(self.resCollection, self.resGeoFeature.collections.all())
        self.assertIn(self.resCollection, self.resModelInstance.collections.all())
        self.assertIn(self.resCollection, self.resTimeSeries.collections.all())

        # test remove all res from collection.resources
        self.resCollection.resources.clear()
        self.assertEqual(self.resCollection.resources.count(), 0)

        # test collection NOT in res.collections
        self.assertNotIn(self.resCollection, self.resGen1.collections.all())
        self.assertNotIn(self.resCollection, self.resGeoFeature.collections.all())
        self.assertNotIn(self.resCollection, self.resModelInstance.collections.all())
        self.assertNotIn(self.resCollection, self.resTimeSeries.collections.all())

        # test adding same resources to multiple collection resources
        self.resCollection.resources.add(self.resGen1)
        self.resCollection.resources.add(self.resGeoFeature)
        self.resCollection_with_missing_metadata.resources.add(self.resGen1)
        self.resCollection_with_missing_metadata.resources.add(self.resGeoFeature)

        # test resources are in both collection resource
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGeoFeature, self.resCollection.resources.all())
        self.assertIn(self.resGen1, self.resCollection_with_missing_metadata.resources.all())
        self.assertIn(self.resGeoFeature, self.resCollection_with_missing_metadata.resources.all())

    def test_collection_deleted_resource(self):
        # test CollectionDeletedResource

        self.assertEqual(self.resCollection.deleted_resources.count(), 0)
        self.assertEqual(CollectionDeletedResource.objects.count(), 0)
        # create 2 CollectionDeletedResource obj and associate with collection
        CollectionDeletedResource.objects.create(resource_title=self.resGen1.metadata.title,
                                                 deleted_by=self.user1,
                                                 collection=self.resCollection)
        CollectionDeletedResource.objects.create(resource_title=self.resModelInstance.metadata.title,
                                                 deleted_by=self.user1,
                                                 collection=self.resCollection)

        self.assertEqual(CollectionDeletedResource.objects.count(), 2)
        self.assertEqual(self.resCollection.deleted_resources.count(), 2)
        self.assertEqual(self.resCollection.deleted_resources.filter(resource_title=
                                                                     self.resGen1.metadata.title).count(), 1)
        self.assertEqual(self.resCollection.deleted_resources.filter(resource_title=
                                                                     self.resModelInstance.metadata.title).count(), 1)

        # remove CollectionDeletedResource objs
        self.resCollection.deleted_resources.all().delete()
        self.assertEqual(CollectionDeletedResource.objects.count(), 0)
        self.assertEqual(self.resCollection.deleted_resources.count(), 0)

    def test_update_collection_own_permission(self):
        # test update_collection()

        self.assertEqual(self.resCollection.resources.count(), 0)
        self.assertFalse(self.resCollection.can_be_public_or_discoverable)
        url_to_update_collection = self.url_to_update_collection.format(self.resCollection.short_id)

        # anonymous user
        # should inform frontend error
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen1.short_id, self.resGen2.short_id,
                                                              self.resGen3.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "error")
        self.assertEqual(resp_json["metadata_status"], "Insufficient to make public")
        self.assertFalse(self.resCollection.can_be_public_or_discoverable)

        # user 1 login
        self.api_client.login(username='user1', password='mypassword1')

        # add 3 private member resources
        # should inform frontend "sufficient to make public"
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen1.short_id, self.resGen2.short_id,
                                                              self.resGen3.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["metadata_status"], "Sufficient to make public")
        self.assertTrue(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 3)
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGen2, self.resCollection.resources.all())
        self.assertIn(self.resGen3, self.resCollection.resources.all())

        # remove renGen2 (just add 1 and 3)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen1.short_id, self.resGen3.short_id]},
                                        )
        resp_json = json.loads(response.content)
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
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["metadata_status"], "Insufficient to make public")
        self.assertFalse(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 0)

        # add resGen1, resGen2, and resGen4 (no permission)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen1.short_id, self.resGen2.short_id,
                                                              self.resGen4.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "error")
        self.assertEqual(self.resCollection.resources.count(), 0)

        # add resGen1 and resGen3
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen1.short_id, self.resGen3.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["metadata_status"], "Sufficient to make public")
        self.assertTrue(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 2)
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGen3, self.resCollection.resources.all())

        # remove resGen1 and resGen3, add resGen2 and resGen4 (no permission)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen2.short_id, self.resGen4.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "error")
        self.assertEqual(self.resCollection.resources.count(), 2)
        self.assertIn(self.resGen1, self.resCollection.resources.all())
        self.assertIn(self.resGen3, self.resCollection.resources.all())

        # grants View permission to User 1 over resGen4
        self.user2.uaccess.share_resource_with_user(self.resGen4, self.user1, PrivilegeCodes.VIEW)

        # remove resGen1 and resGen3, add resGen2 and resGen4 (having permission)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen2.short_id, self.resGen4.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertTrue(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 2)
        self.assertIn(self.resGen2, self.resCollection.resources.all())
        self.assertIn(self.resGen4, self.resCollection.resources.all())

        # test adding resources to a collection that does not have all the required metadata
        self.assertEqual(self.resCollection_with_missing_metadata.resources.count(), 0)
        url_to_update_collection = self.url_to_update_collection.format(
            self.resCollection_with_missing_metadata.short_id)

        self.assertFalse(self.resCollection_with_missing_metadata.can_be_public_or_discoverable)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen1.short_id, self.resGen2.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertFalse(self.resCollection_with_missing_metadata.can_be_public_or_discoverable)

    def test_update_collection_edit_permission(self):
        self.assertEqual(self.resCollection.resources.count(), 0)
        url_to_update_collection = self.url_to_update_collection.format(self.resCollection.short_id)

        # User 2 login
        self.api_client.login(username='user2', password='mypassword2')

        # User 2: add resGen4 in to collection (User 2 has no permission over this collection)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen4.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "error")
        self.assertFalse(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 0)

        # grants View permission to User 2 over collection
        self.user1.uaccess.share_resource_with_user(self.resCollection, self.user2, PrivilegeCodes.VIEW)

        # User 2: add resGen4 in to collection (User 2 has View permission over this collection that is not enough)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen4.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "error")
        self.assertFalse(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 0)

        # grants Change permission to User 2 over collection
        self.user1.uaccess.share_resource_with_user(self.resCollection, self.user2, PrivilegeCodes.CHANGE)

        # User 2: add resGen4 in to collection (User 2 has Change permission over this collection)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen4.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertTrue(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 1)
        self.assertIn(self.resGen4, self.resCollection.resources.all())

        # User 2: remove resGen4 and add resGen3 (no permission)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen3.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "error")
        self.assertTrue(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 1)
        self.assertIn(self.resGen4, self.resCollection.resources.all())

        # grants View permission to User 2 over renGen3
        self.user1.uaccess.share_resource_with_user(self.resGen3, self.user2, PrivilegeCodes.VIEW)

        # User 2: remove resGen4 and add resGen3 (View permission)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen3.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertTrue(self.resCollection.can_be_public_or_discoverable)
        self.assertEqual(self.resCollection.resources.count(), 1)
        self.assertIn(self.resGen3, self.resCollection.resources.all())

    def test_adding_one_collection_to_another_collection(self):
        # a collection resource can't be added to another collection resource

        url_to_update_collection = self.url_to_update_collection.format(self.resCollection.short_id)
        # this collection should contain no resources at this point
        self.assertEquals(self.resCollection.resources.count(), 0)
        # user 1 login
        self.api_client.login(username='user1', password='mypassword1')

        # add one collection resource to another collection resource
        # json response status should be error
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resCollection_with_missing_metadata.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "error")
        # collection still should have no resources
        self.assertEquals(self.resCollection.resources.count(), 0)

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
        url_to_delete_resource_for_resGen1 = self.url_to_delete_resource.format(self.resGen1.short_id)
        self.api_client.post(url_to_delete_resource_for_resGen1, HTTP_REFERER='http://foo/bar')

        # delete resGen2
        res_id_resGen2 = self.resGen2.short_id
        url_to_delete_resource_for_resGen2 = self.url_to_delete_resource.format(self.resGen2.short_id)
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
        url_to_update_collection_for_deleted_resources = self.url_to_update_collection_for_deleted_resources.format(
            self.resCollection.short_id)

        # log out User 1
        self.api_client.logout()
        # log in as User 2
        self.api_client.login(username='user2', password='mypassword2')

        # User 2 update_collection_for_deleted_resources --> error
        response = self.api_client.post(url_to_update_collection_for_deleted_resources)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "error")
        self.assertEqual(self.resCollection.deleted_resources.count(), 2)

        # logout and login as User 1
        self.api_client.logout()
        self.api_client.login(username='user1', password='mypassword1')

        # User 1update_collection_for_deleted_resources --> success
        response = self.api_client.post(url_to_update_collection_for_deleted_resources)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        # there should be now no tracked deleted resources for the collection
        self.assertEqual(self.resCollection.deleted_resources.count(), 0)
        self.assertEqual(CollectionDeletedResource.objects.count(), 0)

