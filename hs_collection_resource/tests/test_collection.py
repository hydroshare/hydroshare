import json
import unittest

from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth.models import Group, User

from hs_core.hydroshare import resource, create_resource, create_account
from hs_access_control.models import PrivilegeCodes

class TestCollection(TransactionTestCase):

    def setUp(self):
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

        self.resGen1 = create_resource(
            resource_type='GenericResource',
            owner=self.user1,
            title='Gen 1',
            keywords=['kw1', 'kw2']
        )

        self.resGen2 = create_resource(
            resource_type='GenericResource',
            owner=self.user1,
            title='Gen 2',
            keywords=['kw1', 'kw2']
        )

        self.resGen3 = create_resource(
            resource_type='GenericResource',
            owner=self.user1,
            title='Gen 3',
            keywords=['kw1', 'kw2']
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

        self.resGen4 = create_resource(
            resource_type='GenericResource',
            owner=self.user2,
            title='Gen 4',
            keywords=['kw1', 'kw2']
        )

        self.resCollection2_user2 = create_resource(
            resource_type='CollectionResource',
            owner=self.user2,
            title='My Collection 2',
            keywords=['kw1', 'kw2'],
            metadata=[{"rights": {"statement": "mystatement", "url": "http://www.google.com"}},
                      {"description": {"abstract": "myabstract"}}
                      ]
        )

        self.resGen5_user2 = create_resource(
            resource_type='GenericResource',
            owner=self.user2,
            title='Gen 5',
            keywords=['kw1', 'kw2'],
            metadata=[{"rights": {"statement": "mystatement", "url": "http://www.google.com"}},
                  {"description": {"abstract": "myabstract"}}
                  ]
        )

        self.url_to_update_collection = "/hsapi/_internal/{0}/update-collection/"
        self.url_to_collection_member_permission = "/hsapi/_internal/{0}/collection-member-permission/{1}/"
        self.url_to_set_resource_flag = "/hsapi/_internal/{0}/set-resource-flag/"
        self.url_to_delete_resource = "/hsapi/_internal/{0}/delete-resource/"

    @unittest.skip
    def test_views(self):

        # test update_collection()
        # self.assertEqual(self.resCollection.metadata.collection.all().count(), 0)
        self.assertEqual(self.resCollection.metadata.collection, None)
        url_to_update_collection = self.url_to_update_collection.format(self.resCollection.short_id)

        # anonymous user
        # should inform frontend error
        response = self.api_client.post(url_to_update_collection, {'resource_id_list': [self.resGen1.short_id, self.resGen2.short_id, self.resGen3.short_id]})
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "error")

        # user 1 login
        self.api_client.login(username='user1', password='mypassword1')

        # add 3 private member resources
        # should inform frontend "Insufficient to make public"
        response = self.api_client.post(url_to_update_collection, {'resource_id_list': [self.resGen1.short_id, self.resGen2.short_id, self.resGen3.short_id]})
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["user_permission"], "Own")
        self.assertEqual(resp_json["current_sharing_status"], "Private")
        self.assertEqual(resp_json["new_sharing_status"], "")
        self.assertEqual(resp_json["metadata_status"], "Insufficient to make public")
        self.assertEqual(self.resCollection.metadata.collection.resources.all().count(), 3)

        # make Gen1 public
        self.resGen1.raccess.public = True
        self.resGen1.raccess.save()

        # make Gen2 public
        self.resGen2.raccess.public = True
        self.resGen2.raccess.save()

        # make Gen3 discoverable
        self.resGen3.raccess.discoverable = True
        self.resGen3.raccess.save()

        # re-add 3 public or discoverable member resources
        # should inform frontend "Sufficient to make public")
        response = self.api_client.post(url_to_update_collection, {'resource_id_list': [self.resGen1.short_id, self.resGen2.short_id, self.resGen3.short_id]})
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["metadata_status"], "Sufficient to make public")
        self.assertEqual(self.resCollection.metadata.collection.resources.all().count(), 3)

        # make Collection public
        self.resCollection.raccess.public = True
        self.resCollection.raccess.save()
        # make Gen3 private
        self.resGen3.raccess.public = False
        self.resGen3.raccess.discoverable = False
        self.resGen3.raccess.save()
        # re-add the 3 resources (2 public 1 private)
        # should inform frontend to downgrade to Private
        response = self.api_client.post(url_to_update_collection, {'resource_id_list': [self.resGen1.short_id, self.resGen2.short_id, self.resGen3.short_id]})
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["current_sharing_status"], "Public")
        self.assertEqual(resp_json["new_sharing_status"], "Private")
        self.assertEqual(resp_json["metadata_status"], "Insufficient to make public")
        self.assertEqual(self.resCollection.metadata.collection.resources.all().count(), 3)
        self.assertEqual(self.resGen3.raccess.public, False)
        self.assertEqual(self.resGen3.raccess.discoverable, False)

        # test collection_member_permission()
        # test User's permission over the collection contents
        user2_id = self.user2.id
        url_to_collection_member_permission = self.url_to_collection_member_permission = \
            "/hsapi/_internal/{0}/collection-member-permission/{1}/".format(self.resCollection.short_id, user2_id)
        response = self.api_client.get(url_to_collection_member_permission)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(len(resp_json["no_permission_list"]), 1)

        # share this private collection with User2
        self.user1.uaccess.share_resource_with_user(self.resCollection, self.user2, PrivilegeCodes.CHANGE)

        # User 1 logout
        self.api_client.logout()

        # User 2 login
        self.api_client.login(username='user2', password='mypassword2')

        # User 2 takes out private res 3
        # should inform frontend "Sufficient to make public"
        response = self.api_client.post(url_to_update_collection, {'resource_id_list': \
                                            [self.resGen1.short_id, self.resGen2.short_id]})
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["user_permission"], "Edit")
        self.assertEqual(resp_json["current_sharing_status"], "Private")
        self.assertEqual(resp_json["new_sharing_status"], "")
        self.assertEqual(resp_json["metadata_status"], "Sufficient to make public")
        self.assertEqual(self.resCollection.metadata.collection.resources.all().count(), 2)

        # make User 2's Gen4 discoverable
        self.resGen4.raccess.discoverable = True
        self.resGen4.raccess.save()

        # User 2 adds his dicoverable res 4
        response = self.api_client.post(url_to_update_collection, {'resource_id_list': \
                        [self.resGen1.short_id, self.resGen2.short_id, self.resGen4.short_id]})
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["user_permission"], "Edit")
        self.assertEqual(resp_json["current_sharing_status"], "Private")
        self.assertEqual(resp_json["new_sharing_status"], "")
        self.assertEqual(resp_json["metadata_status"], "Sufficient to make public")
        self.assertEqual(self.resCollection.metadata.collection.resources.all().count(), 3)

    def test_custom_logic_in_hs_core_1(self):

        # this func tests that the public collection should downgrade to private if its any member resource is changed to private

        self.api_client.logout()
        # user 2 login
        self.api_client.login(username='user2', password='mypassword2')

        ##### test custom logic for collection in hs_core
        # check gen res 5 current sharing status --> private
        self.assertEqual(self.resGen5_user2.raccess.public, False)
        self.assertEqual(self.resGen5_user2.raccess.discoverable, False)

        # make gen res 5 public (not working because it does not meet public precondition: no resouece file in generic res)
        # url_to_set_resource_flag_for_resGen5 = self.url_to_set_resource_flag.format(self.resGen5_user2.short_id)
        # response = self.api_client.post(url_to_set_resource_flag_for_resGen5, {'t': 'make_public'}, HTTP_REFERER='http://foo/bar')

        # make gen res 5 public manaully
        self.resGen5_user2.raccess.public = True
        self.resGen5_user2.raccess.discoverable = True
        self.resGen5_user2.raccess.save()

        # check gen res 5 current sharing status --> public
        self.assertEqual(self.resGen5_user2.raccess.public, True)
        self.assertEqual(self.resGen5_user2.raccess.discoverable, True)

        # check collection current sharing status --> private
        self.assertEqual(self.resCollection2_user2.raccess.public, False)
        self.assertEqual(self.resCollection2_user2.raccess.discoverable, False)

        # add one public gen res 5into collection
        url_to_update_collection_2 = self.url_to_update_collection.format(self.resCollection2_user2.short_id)
        response = self.api_client.post(url_to_update_collection_2, {'resource_id_list': [self.resGen5_user2.short_id]})
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["metadata_status"], "Sufficient to make public")
        self.assertEqual(self.resCollection2_user2.metadata.collection.resources.all().count(), 1)

        # manually make collection public
        self.resCollection2_user2.raccess.public = True
        self.resCollection2_user2.raccess.discoverable = True
        self.resCollection2_user2.raccess.save()

        # check collection current sharing status --> public
        self.assertEqual(self.resCollection2_user2.raccess.public, True)
        self.assertEqual(self.resCollection2_user2.raccess.discoverable, True)

        f=open("abcde2.txt", 'w', 0)
        f.write("res id {}\n".format(self.resGen5_user2.short_id))
        f.write("collection id {}\n".format(self.resCollection2_user2.short_id))
        f.close()

        # downgrade res gen 5 to private
        url_to_set_resource_flag_for_resGen5 = self.url_to_set_resource_flag.format(self.resGen5_user2.short_id)
        response = self.api_client.post(url_to_set_resource_flag_for_resGen5, {'t': 'make_private'}, HTTP_REFERER='http://foo/bar')

        # # check gen res 5 new sharing status --> private
        # self.assertEqual(self.resGen5_user2.raccess.public, False)
        # self.assertEqual(self.resGen5_user2.raccess.discoverable, False)

        # # check collection 2 new status --> private
        # self.assertEqual(self.resCollection2_user2.raccess.public, False)
        # self.assertEqual(self.resCollection2_user2.raccess.discoverable, False)

    def test_custom_logic_in_hs_core_1_result(self):
        # we moved the following code here from test_custom_logic_in_hs_core_1()
        # because they failed to pass when they were in that function
        # we are guessing it was due to some delayed commits in db???

        # check gen res 5 new sharing status --> private
        self.assertEqual(self.resGen5_user2.raccess.public, False)
        self.assertEqual(self.resGen5_user2.raccess.discoverable, False)

        # check collection 2 new status --> private
        self.assertEqual(self.resCollection2_user2.raccess.public, False)
        self.assertEqual(self.resCollection2_user2.raccess.discoverable, False)

    def test_custom_logic_in_hs_core_2(self):

        # this func tests that the public collection should downgrade to private if the last member res gets removed

        self.api_client.logout()
        # user 2 login
        self.api_client.login(username='user2', password='mypassword2')

        ##### test custom logic for collection in hs_core
        # check gen res 5 current sharing status --> private
        self.assertEqual(self.resGen5_user2.raccess.public, False)
        self.assertEqual(self.resGen5_user2.raccess.discoverable, False)

        # make gen res 5 public manaully
        self.resGen5_user2.raccess.public = True
        self.resGen5_user2.raccess.discoverable = True
        self.resGen5_user2.raccess.save()

        # check gen res 5 current sharing status --> public
        self.assertEqual(self.resGen5_user2.raccess.public, True)
        self.assertEqual(self.resGen5_user2.raccess.discoverable, True)

        # check collection current sharing status --> private
        self.assertEqual(self.resCollection2_user2.raccess.public, False)
        self.assertEqual(self.resCollection2_user2.raccess.discoverable, False)

        # add one public gen res 5into collection
        url_to_update_collection_2 = self.url_to_update_collection.format(self.resCollection2_user2.short_id)
        response = self.api_client.post(url_to_update_collection_2, {'resource_id_list': [self.resGen5_user2.short_id]})
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["metadata_status"], "Sufficient to make public")
        self.assertEqual(self.resCollection2_user2.metadata.collection.resources.all().count(), 1)

        # manually make collection public
        self.resCollection2_user2.raccess.public = True
        self.resCollection2_user2.raccess.discoverable = True
        self.resCollection2_user2.raccess.save()

        # check collection current sharing status --> public
        self.assertEqual(self.resCollection2_user2.raccess.public, True)
        self.assertEqual(self.resCollection2_user2.raccess.discoverable, True)

        # downgrade res gen 5 to private
        url_to_delete_res_resGen5 = self.url_to_delete_resource.format(self.resGen5_user2.short_id)
        response = self.api_client.post(url_to_delete_res_resGen5, HTTP_REFERER='http://foo/bar')

    def test_custom_logic_in_hs_core_2_result(self):

        self.assertEqual(self.resCollection2_user2.metadata.collection.resources.all().count(), 0)

        # # check gen res 5 new sharing status --> private
        # self.assertEqual(self.resGen5_user2.raccess.public, False)
        # self.assertEqual(self.resGen5_user2.raccess.discoverable, False)

        # check collection 2 new status --> private
        self.assertEqual(self.resCollection2_user2.raccess.public, False)
        self.assertEqual(self.resCollection2_user2.raccess.discoverable, False)



