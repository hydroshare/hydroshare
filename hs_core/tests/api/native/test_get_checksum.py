__author__ = 'Tian Gan'

## unit test for get_checksum() from resource.py


from django.test import TestCase
from django.contrib.auth.models import User, Group
from hs_core import hydroshare
from hs_core.models import GenericResource


class TestGetChecksum(TestCase):
    def setUp(self):
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

    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()

    def test_get_checksum(self):
        self.assertRaises(
            NotImplementedError,
            lambda: hydroshare.get_checksum(self.res.pk)
        )
