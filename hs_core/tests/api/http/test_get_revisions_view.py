__author__ = 'shaunjl'

"""
Tastypie REST API tests for resolveDOI(view) modeled entirely after
test_get_revisions.py written by Pabitra Dash

"""
from tastypie.test import ResourceTestCase, TestApiClient
from django.contrib.auth.models import User
from hs_core import hydroshare
from tastypie.serializers import Serializer


class TestGetRevisionsAPI(ResourceTestCase):

    serializer = Serializer()

    def setUp(self):
        self.api_client = TestApiClient()
        user = hydroshare.create_account(   
            'shaun@gmail.com',
            username='user0',
            first_name='User0_FirstName',
            last_name='User0_LastName',
        )
        self.res = hydroshare.create_resource('GenericResource', user, 'myres')

    def tearDown(self):
        User.objects.all().delete()
        hydroshare.delete_resource(self.res.short_id)

    def test_get_revisions(self):
        url = 'hsapi/revisions/{0}/'.format(self.res.short_id)
        resp = self.api_client.get(url)
        res_revisions = self.deserialize(resp)
        
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(res_revisions), 1)
        self.assertEqual(hydroshare.get_revisions(self.res.short_id), res_revisions)

        resource_changed_by = hydroshare.create_account(
            'shaunl@gmail.com',
            username='user1',
            first_name='User1_FirstName',
            last_name='User1_LastName'
        )
        hydroshare.utils.resource_modified(self.res, resource_changed_by)
        resp = self.api_client.get(url)
        res_revisions = self.deserialize(resp)

        self.assertValidJSONResponse(resp)
        self.assertEqual(len(res_revisions), 2)
        self.assertEqual(hydroshare.get_revisions(self.res.short_id), res_revisions)

        # test that each revision has a different time stamp
        self.assertNotEqual(res_revisions[0].timestamp, res_revisions[1].timestamp)

        # test that each resource revision has the same resource id
        for bags in res_revisions:
            self.assertEqual(self.res.id, bags.object_id)

        # add a file to the resource to generate another revision of the resource
        # create a file
        original_file_name = 'original.txt'
        original_file = open(original_file_name, 'w')
        original_file.write("original text")
        original_file.close()

        original_file = open(original_file_name, 'r')
        # add the file to the resource
        hydroshare.add_resource_files(self.res.short_id, original_file)
        resp = self.api_client.get(url)
        res_revisions = self.deserialize(resp)

        self.assertValidJSONResponse(resp)
        # test that we now have 3 revisions
        self.assertEqual(len(res_revisions), 3)
        self.assertEqual(hydroshare.get_revisions(self.res.short_id), res_revisions)
        
        # test that each revision has a different time stamp
        self.assertNotEqual(res_revisions[0].timestamp, res_revisions[1].timestamp)
        self.assertNotEqual(res_revisions[0].timestamp, res_revisions[2].timestamp)
        self.assertNotEqual(res_revisions[1].timestamp, res_revisions[2].timestamp)

        # delete the file in the resource to create another revision of the resource
        hydroshare.delete_resource_file(self.res.short_id, original_file_name)
        resp = self.api_client.get(url)
        res_revisions = self.deserialize(resp)

        self.assertValidJSONResponse(resp)
        self.assertEqual(hydroshare.get_revisions(self.res.short_id), res_revisions)
        # test that we now have 4 revisions
        self.assertEqual(len(res_revisions), 4)

