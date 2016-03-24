import os
import shutil
import tempfile
import json

from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import UploadedFile

from hs_core.hydroshare import utils
from hs_core.hydroshare import resource, create_resource, create_account
from hs_core.models import BaseResource
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

        self.temp_dir = tempfile.mkdtemp()
        self.res_file_name = 'my_res_file.txt'
        self.res_file = 'hs_collection_resource/tests/{}'.format(self.res_file_name)
        target_temp_res_file = os.path.join(self.temp_dir, self.res_file_name)
        shutil.copy(self.res_file, target_temp_res_file)
        self.res_file_obj = open(target_temp_res_file, 'r')

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
            keywords=['kw1', 'kw2'],
            metadata=[{"rights": {"statement": "mystatement", "url": "http://www.google.com"}},
                  {"description": {"abstract": "myabstract"}}
                  ]
        )

        self.resGen2 = create_resource(
            resource_type='GenericResource',
            owner=self.user1,
            title='Gen 2',
            keywords=['kw1', 'kw2'],
            metadata=[{"rights": {"statement": "mystatement", "url": "http://www.google.com"}},
            {"description": {"abstract": "myabstract"}}
            ]
        )

        self.resGen3 = create_resource(
            resource_type='GenericResource',
            owner=self.user1,
            title='Gen 3',
            keywords=['kw1', 'kw2'],
            metadata=[{"rights": {"statement": "mystatement", "url": "http://www.google.com"}},
            {"description": {"abstract": "myabstract"}}
            ]
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
            keywords=['kw1', 'kw2'],
            metadata=[{"rights": {"statement": "mystatement", "url": "http://www.google.com"}},
            {"description": {"abstract": "myabstract"}}
            ]
        )

        self.url_to_update_collection = "/hsapi/_internal/{0}/update-collection/"
        self.url_to_collection_member_permission = "/hsapi/_internal/{0}/collection-member-permission/{1}/"
        self.url_to_set_resource_flag = "/hsapi/_internal/{0}/set-resource-flag/"
        self.url_to_delete_resource = "/hsapi/_internal/{0}/delete-resource/"

    def tearDown(self):
        super(TestCollection, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_views_own_permission(self):
        # test update_collection()
        self.assertEqual(self.resCollection.resources.count(), 0)
        url_to_update_collection = self.url_to_update_collection.format(self.resCollection.short_id)

        # anonymous user
        # should inform frontend error
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen1.short_id, self.resGen2.short_id, self.resGen3.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "error")
        self.assertEqual(resp_json["metadata_status"], "Insufficient to make public")

        # user 1 login
        self.api_client.login(username='user1', password='mypassword1')

        # add 3 private member resources
        # should inform frontend "Insufficient to make public"
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen1.short_id, self.resGen2.short_id, self.resGen3.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(resp_json["metadata_status"], "Sufficient to make public")
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
        self.assertEqual(self.resCollection.resources.count(), 0)

        # add resGen1, resGen2, and resGen4 (no permission)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen1.short_id, self.resGen2.short_id,self.resGen4.short_id]},
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
        self.assertEqual(self.resCollection.resources.count(), 2)
        self.assertIn(self.resGen2, self.resCollection.resources.all())
        self.assertIn(self.resGen4, self.resCollection.resources.all())

    def test_views_edit_permission(self):

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
        self.assertEqual(self.resCollection.resources.count(), 0)


        # grants View permission to User 2 over collection
        self.user1.uaccess.share_resource_with_user(self.resCollection, self.user2, PrivilegeCodes.VIEW)

        # User 2: add resGen4 in to collection (User 2 has View permission over this collection that is not enough)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen4.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "error")
        self.assertEqual(self.resCollection.resources.count(), 0)

        # grants Change permission to User 2 over collection
        self.user1.uaccess.share_resource_with_user(self.resCollection, self.user2, PrivilegeCodes.CHANGE)

        # User 2: add resGen4 in to collection (User 2 has Change permission over this collection)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen4.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(self.resCollection.resources.count(), 1)
        self.assertIn(self.resGen4, self.resCollection.resources.all())


        # User 2: remove resGen4 and add resGen3 (no permission)
        response = self.api_client.post(url_to_update_collection,
                                        {'resource_id_list': [self.resGen3.short_id]},
                                        )
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["status"], "error")
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
        self.assertEqual(self.resCollection.resources.count(), 1)
        self.assertIn(self.resGen3, self.resCollection.resources.all())



    # def test_custom_logic_in_hs_core_part_1(self):
    #     # test custom logic for collection in hs_core
    #     # this func tests that public collection should downgrade to private automatically if its any member resource is changed to private
    #
    #     # user 1 login
    #     self.api_client.login(username='user1', password='mypassword1')
    #
    #     # no res file has been uploaded
    #     self.assertFalse(self.resGen1.has_required_content_files())
    #     # all required metadata terms have been provided when creating it
    #     self.assertTrue(self.resGen1.metadata.has_all_required_elements())
    #     self.assertFalse(self.resGen1.can_be_public_or_discoverable)
    #
    #     # check resGen1 current sharing status --> private
    #     self.assertEqual(self.resGen1.raccess.public, False)
    #     self.assertEqual(self.resGen1.raccess.discoverable, False)
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resGen1.short_id).raccess.public, False)
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resGen1.short_id).raccess.discoverable, False)
    #
    #     # add a res file to resGen1
    #     files = [UploadedFile(file=self.res_file_obj, name=self.res_file_name)]
    #     utils.resource_file_add_pre_process(resource=self.resGen1, files=files, user=self.user1,
    #                                         extract_metadata=False)
    #
    #     utils.resource_file_add_process(resource=self.resGen1, files=files, user=self.user1,
    #                                     extract_metadata=True)
    #
    #     # check resGen can_be_public_or_discoverable again --> True
    #     self.assertTrue(self.resGen1.has_required_content_files())
    #     self.assertTrue(self.resGen1.metadata.has_all_required_elements())
    #     self.assertTrue(self.resGen1.can_be_public_or_discoverable)
    #
    #     # make resGen1 public
    #     url_to_set_resource_flag_for_resGen1 = self.url_to_set_resource_flag.format(self.resGen1.short_id)
    #     response = self.api_client.post(url_to_set_resource_flag_for_resGen1, {'t': 'make_public'}, HTTP_REFERER='http://foo/bar')
    #
    #     # check resGen1 new  sharing status --> public
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resGen1.short_id).raccess.public, True)
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resGen1.short_id).raccess.discoverable, True)
    #     ## the following two statements return wrong sharing status. DONT KNOW WHY!!!
    #     # self.assertEqual(self.resGen1.raccess.public, True)
    #     # self.assertEqual(self.resGen1.raccess.discoverable, True)
    #
    #     # check resCollection current sharing status --> private
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resCollection.short_id).raccess.public, False)
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resCollection.short_id).raccess.discoverable, False)
    #     self.assertEqual(self.resCollection.raccess.public, False)
    #     self.assertEqual(self.resCollection.raccess.discoverable, False)
    #
    #     # check resCollection can_be_public_or_discoverable again --> False
    #     # collection does not need res files
    #     self.assertTrue(self.resCollection.has_required_content_files())
    #     # collection should have at least on member resource
    #     self.assertFalse(self.resCollection.metadata.has_all_required_elements())
    #     # False
    #     self.assertFalse(self.resCollection.can_be_public_or_discoverable)
    #
    #     # add one public resGen1 into resCollection
    #     url_to_update_resCollection = self.url_to_update_collection.format(self.resCollection.short_id)
    #     response = self.api_client.post(url_to_update_resCollection,
    #                                     {'resource_id_list': [self.resGen1.short_id]},
    #                                     HTTP_REFERER='http://foo/bar')
    #     resp_json = json.loads(response.content)
    #     self.assertEqual(resp_json["status"], "success")
    #     self.assertEqual(resp_json["metadata_status"], "Sufficient to make public")
    #     self.assertEqual(self.resCollection.metadata.collection.resources.all().count(), 1)
    #
    #     # make resCollection public
    #     url_to_set_resource_flag_for_resCollection = self.url_to_set_resource_flag.format(self.resCollection.short_id)
    #     response = self.api_client.post(url_to_set_resource_flag_for_resCollection, {'t': 'make_public'}, HTTP_REFERER='http://foo/bar')
    #
    #     # check resCollection current sharing status --> public
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resCollection.short_id).raccess.public, True)
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resCollection.short_id).raccess.discoverable, True)
    #     # the following two statements return wrong sharing status. DONT KNOW WHY!!!
    #     # self.assertEqual(self.resCollection.raccess.public, True)
    #     # self.assertEqual(self.resCollection.raccess.discoverable, True)
    #
    #     # downgrade resGen1 to private
    #     url_to_set_resource_flag_for_resGen1 = self.url_to_set_resource_flag.format(self.resGen1.short_id)
    #     response = self.api_client.post(url_to_set_resource_flag_for_resGen1, {'t': 'make_private'}, HTTP_REFERER='http://foo/bar')
    #
    #     # check resGen1 sharing status --> private
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resGen1.short_id).raccess.public, False)
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resGen1.short_id).raccess.discoverable, False)
    #     # self.assertEqual(self.resGen1.raccess.public, False)
    #     # self.assertEqual(self.resGen1.raccess.discoverable, False)
    #
    #     # check resCollection new status --> private
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resCollection.short_id).raccess.public, False)
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resCollection.short_id).raccess.discoverable, False)
    #     # self.assertEqual(self.resCollection.raccess.public, False)
    #     # self.assertEqual(self.resCollection.raccess.discoverable, False)
    #
    # def test_custom_logic_in_hs_core_part_2(self):
    #     # test custom logic for collection in hs_core
    #     # this func tests that the public collection should downgrade to private if the last member res gets removed
    #
    #     # user 1 login
    #     self.api_client.login(username='user1', password='mypassword1')
    #
    #     # no res file has been uploaded
    #     self.assertFalse(self.resGen1.has_required_content_files())
    #     # all required metadata terms have been provided when creating it
    #     self.assertTrue(self.resGen1.metadata.has_all_required_elements())
    #     self.assertFalse(self.resGen1.can_be_public_or_discoverable)
    #
    #     # check resGen1 current sharing status --> private
    #     self.assertEqual(self.resGen1.raccess.public, False)
    #     self.assertEqual(self.resGen1.raccess.discoverable, False)
    #     # we double check its sharing status using a different statement
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resGen1.short_id).raccess.public, False)
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resGen1.short_id).raccess.discoverable, False)
    #
    #     # add a res file to resGen1
    #     files = [UploadedFile(file=self.res_file_obj, name=self.res_file_name)]
    #     utils.resource_file_add_pre_process(resource=self.resGen1, files=files, user=self.user1,
    #                                         extract_metadata=False)
    #
    #     utils.resource_file_add_process(resource=self.resGen1, files=files, user=self.user1,
    #                                     extract_metadata=True)
    #
    #     # check resGen can_be_public_or_discoverable again --> True
    #     self.assertTrue(self.resGen1.has_required_content_files())
    #     self.assertTrue(self.resGen1.metadata.has_all_required_elements())
    #     self.assertTrue(self.resGen1.can_be_public_or_discoverable)
    #
    #     # make resGen1 public
    #     url_to_set_resource_flag_for_resGen1 = self.url_to_set_resource_flag.format(self.resGen1.short_id)
    #     response = self.api_client.post(url_to_set_resource_flag_for_resGen1, {'t': 'make_public'}, HTTP_REFERER='http://foo/bar')
    #
    #     # check resGen1 new  sharing status --> public
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resGen1.short_id).raccess.public, True)
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resGen1.short_id).raccess.discoverable, True)
    #     # self.assertEqual(self.resGen1.raccess.public, True)
    #     # self.assertEqual(self.resGen1.raccess.discoverable, True)
    #
    #     # check resCollection current sharing status --> private
    #     # we use two different statments to double check sharing status
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resCollection.short_id).raccess.public, False)
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resCollection.short_id).raccess.discoverable, False)
    #     self.assertEqual(self.resCollection.raccess.public, False)
    #     self.assertEqual(self.resCollection.raccess.discoverable, False)
    #
    #     # check resCollection can_be_public_or_discoverable again --> False
    #     # collection does not need res files
    #     self.assertTrue(self.resCollection.has_required_content_files())
    #     # collection should have at least on member resource --> False
    #     self.assertFalse(self.resCollection.metadata.has_all_required_elements())
    #     # False
    #     self.assertFalse(self.resCollection.can_be_public_or_discoverable)
    #
    #     # add one public resGen1 into resCollection
    #     url_to_update_resCollection = self.url_to_update_collection.format(self.resCollection.short_id)
    #     response = self.api_client.post(url_to_update_resCollection, {'resource_id_list': [self.resGen1.short_id]},
    #                                     HTTP_REFERER='http://foo/bar')
    #     resp_json = json.loads(response.content)
    #     self.assertEqual(resp_json["status"], "success")
    #     self.assertEqual(resp_json["metadata_status"], "Sufficient to make public")
    #     self.assertEqual(self.resCollection.metadata.collection.resources.all().count(), 1)
    #
    #     # make resCollection public
    #     url_to_set_resource_flag_for_resCollection = self.url_to_set_resource_flag.format(self.resCollection.short_id)
    #     response = self.api_client.post(url_to_set_resource_flag_for_resCollection, {'t': 'make_public'}, HTTP_REFERER='http://foo/bar')
    #
    #     # check resCollection current sharing status --> pubilic
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resCollection.short_id).raccess.public, True)
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resCollection.short_id).raccess.discoverable, True)
    #     # self.assertEqual(self.resCollection.raccess.public, True)
    #     # self.assertEqual(self.resCollection.raccess.discoverable, True)
    #
    #     res_id_resGen1 = self.resGen1.short_id
    #     # delete resGen1
    #     url_to_delete_resource_for_resGen1 = self.url_to_delete_resource.format(self.resGen1.short_id)
    #     response = self.api_client.post(url_to_delete_resource_for_resGen1, HTTP_REFERER='http://foo/bar')
    #
    #     # check resGen1 has been removed
    #     self.assertEqual(BaseResource.objects.filter(short_id=res_id_resGen1).all().count(), 0)
    #
    #     # check resCollection new status --> private
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resCollection.short_id).raccess.public, False)
    #     self.assertEqual(BaseResource.objects.get(short_id=self.resCollection.short_id).raccess.discoverable, False)
    #     # self.assertEqual(self.resCollection.raccess.public, False)
    #     # self.assertEqual(self.resCollection.raccess.discoverable, False)
