from django.contrib.auth.models import Group, User
from django.test import TestCase

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.testing import MockS3TestCaseMixin


class TestGetResourceByShortkeyAPI(MockS3TestCaseMixin, TestCase):
    def setUp(self):
        super(TestGetResourceByShortkeyAPI, self).setUp()
        self.hydroshare_author_group, _ = Group.objects.get_or_create(name='Hydroshare Author')

    def tearDown(self):
        super(TestGetResourceByShortkeyAPI, self).tearDown()
        Group.objects.all().delete()
        User.objects.all().delete()
        self.resource.delete()
        BaseResource.objects.all().delete()

    def test_get_resource_by_shortkey(self):
        # create a user to be used for creating the resource
        self.user_creator = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        # create a resource
        self.resource = hydroshare.create_resource(
            'CompositeResource',
            self.user_creator,
            'My Test Resource'
        )

        # do the test of the api
        self.assertEqual(
            self.resource,
            hydroshare.get_resource_by_shortkey(self.resource.short_id)
        )
