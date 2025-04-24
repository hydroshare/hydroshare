import os
import tempfile

from django.contrib.auth.models import Group
from django.test import TestCase
from haystack.query import SearchQuerySet

from hs_core.hydroshare import resource
from hs_core.hydroshare import users
from hs_core.models import BaseResource
from hs_core.testing import MockS3TestCaseMixin


class TestDeleteResource(MockS3TestCaseMixin, TestCase):

    def setUp(self):
        super(TestDeleteResource, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.tmp_dir = tempfile.mkdtemp()
        # create a user
        self.user = users.create_account(
            'test_user@email.com',
            username='testuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[])

    def test_delete_resource(self):
        new_res = resource.create_resource(
            'CompositeResource',
            self.user,
            'My Test Resource'
        )

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.all().count(), 1, msg="Number of resources not equal to 1")

        # delete the resource - this is the api we are testing
        resource.delete_resource(new_res.short_id)

        # there should be no resource at this point
        self.assertEqual(BaseResource.objects.all().count(), 0, msg="Number of resources not equal to 0")

    def test_delete_resource_public(self):
        # create files
        file_one = os.path.join(self.tmp_dir, "test1.txt")

        file_one_write = open(file_one, "w")
        file_one_write.write("Putting something inside")
        file_one_write.close()

        # open files for read and upload
        self.file_one = open(file_one, "rb")

        # indexing is turned off during test run - however, using the keyword 'INDEX-FOR-TESTING',
        # this specific resource will get indexed.
        new_res = resource.create_resource(
            'CompositeResource',
            self.user,
            'My Test Resource',
            files=(self.file_one,),
            keywords=("one", "two", "INDEX-FOR-TESTING"),
            metadata=[{"description": {"abstract": "myabstract"}}]
        )
        current_index_count = len(SearchQuerySet().all())

        new_res.set_public(True)
        # Retry mechanism to wait for the resource to be indexed
        import time
        for _ in range(5):  # Retry up to 5 times
            if len(SearchQuerySet().all()) == current_index_count + 1:  # Check if the resource is indexed
                break
            else:
                # Wait for a short period before retrying
                time.sleep(1)
        else:
            self.fail("Resource was not indexed in time")

        resource.delete_resource(new_res.short_id)
        for _ in range(5):  # Retry up to 5 times
            if len(SearchQuerySet().all()) == current_index_count:  # Check if the resource is indexed
                break
            else:
                # Wait for a short period before retrying
                time.sleep(1)
        else:
            self.fail("Resource was not indexed in time")
