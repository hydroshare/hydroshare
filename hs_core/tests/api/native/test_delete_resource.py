import tempfile

from django.contrib.auth.models import Group
from django.test import TestCase

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

