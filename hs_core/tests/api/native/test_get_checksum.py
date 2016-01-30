__author__ = 'Tian Gan'

# unit test for get_checksum() from resource.py

from django.contrib.auth.models import User, Group
from django.test import TestCase
from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin


class TestGetChecksum(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestGetChecksum, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user1 = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        # create a resource
        self.res = hydroshare.create_resource(
            'GenericResource',
            self.user1,
            'Test Resource',
        )

    def test_get_checksum(self):
        with self.assertRaises(NotImplementedError):
            hydroshare.get_checksum(self.res.short_id)

