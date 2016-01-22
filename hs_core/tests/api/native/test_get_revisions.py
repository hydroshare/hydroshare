__author__ = 'Pabitra'

import unittest

from django.test import TestCase
from django.contrib.auth.models import User
from hs_core import hydroshare
from hs_core.models import GenericResource

class TestGetRevisionsAPI(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()
        pass

    @unittest.skip
    def test_get_revisions(self):
        # TODO: fix this after resource versioning is implemented
        # create a user to be used for creating the resource
        user_creator = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )
        resource_changed_by = hydroshare.create_account(
            'pabitra.dash@usu.edu',
            username='pkdash',
            first_name='Pabitra',
            last_name='Dash',
            superuser=False,
            groups=[]
        )

        # create a resource
        resource = hydroshare.create_resource('GenericResource', user_creator, 'My resource')

        # test that we have only one revision at this point - this is the api call we are testing
        res_revisions = hydroshare.get_revisions(resource.short_id)
        self.assertEqual(len(res_revisions), 1)

        # set the resource last changed by a different user - to a create another revision of the resource
        hydroshare.utils.resource_modified(resource, resource_changed_by)
        res_revisions = hydroshare.get_revisions(resource.short_id)

        # test that we now have 2 revisions
        self.assertEqual(len(res_revisions), 2)

        # test that each revision has a different time stamp
        self.assertNotEqual(res_revisions[0].timestamp, res_revisions[1].timestamp)

        # test that each resource revision has the same resource id
        for bags in res_revisions:
            self.assertEqual(resource.id, bags.object_id)

        # add a file to the resource to generate another revision of the resource
        # create a file
        original_file_name = 'original.txt'
        original_file = open(original_file_name, 'w')
        original_file.write("original text")
        original_file.close()

        original_file = open(original_file_name, 'r')
        # add the file to the resource
        hydroshare.add_resource_files(resource.short_id, original_file)
        res_revisions = hydroshare.get_revisions(resource.short_id)
        # test that we now have 3 revisions
        self.assertEqual(len(res_revisions), 3)

        # test that each revision has a different time stamp
        self.assertNotEqual(res_revisions[0].timestamp, res_revisions[1].timestamp)
        self.assertNotEqual(res_revisions[0].timestamp, res_revisions[2].timestamp)
        self.assertNotEqual(res_revisions[1].timestamp, res_revisions[2].timestamp)

        # delete the file in the resource to create another revision of the resource
        hydroshare.delete_resource_file(resource.short_id, original_file_name)
        res_revisions = hydroshare.get_revisions(resource.short_id)
        # test that we now have 4 revisions
        self.assertEqual(len(res_revisions), 4)

