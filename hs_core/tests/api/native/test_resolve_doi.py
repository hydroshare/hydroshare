from django.contrib.auth.models import Group
from django.http import Http404
from django.test import TestCase

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin


class TestResolveDOIAPI(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestResolveDOIAPI, self).setUp()
        self.hydroshare_author_group, _ = Group.objects.get_or_create(name='Hydroshare Author')

    def test_resolve_doi(self):
        self.user_creator = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        new_resource = hydroshare.create_resource(
            'GenericResource',
            self.user_creator,
            'My Test Resource'
        )

        # assign doi to the resource
        new_resource.doi = 'xyz'
        new_resource.save()
        # test that the api call resolve_doi() returns the short_id of the resource when we pass the
        # resource doi in this api call
        self.assertEqual(new_resource.short_id, hydroshare.resolve_doi(new_resource.doi))

        # test the exception 'Http404' is raised when we make the api call
        # passing a random doi ( e.g., '123') that does not exist
        with self.assertRaises(Http404):
            hydroshare.resolve_doi("123")
