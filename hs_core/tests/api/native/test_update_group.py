from django.test import TestCase
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from hs_core import hydroshare


class TestUpdateGroupAPI(TestCase):
    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.john_group_owner = hydroshare.create_account(
            'john@gmail.com',
            username='johns',
            first_name='John',
            last_name='Sam',
            superuser=False,
            groups=[]
        )
        self.lisa_not_group_owner = hydroshare.create_account(
            'lisa@gmail.com',
            username='lisaA',
            first_name='Lisa',
            last_name='Anderson',
            superuser=False,
            groups=[]
        )

        self.group = self.john_group_owner.uaccess.create_group(
            title='Modeling Group', description='This group is interested in hydrological '
                                                'modelling')

    def test_set_group_active_status(self):
        """this is to test the util function that sets the group active status flag"""

        # test active status of the group should be True
        self.assertEqual(self.group.gaccess.active, True)
        # This is the utility function we are testing
        hydroshare.set_group_active_status(self.john_group_owner, self.group.id, False)
        # test active status of the group should be False
        self.group = Group.objects.get(id=self.group.id)
        self.assertEqual(self.group.gaccess.active, False)
        # set the active status to True again
        hydroshare.set_group_active_status(self.john_group_owner, self.group.id, True)
        # test active status of the group should be True
        self.group = Group.objects.get(id=self.group.id)
        self.assertEqual(self.group.gaccess.active, True)

        # test for non-group owner trying to set the active status should raise PermissionDenied
        # exception
        with self.assertRaises(PermissionDenied):
            hydroshare.set_group_active_status(self.lisa_not_group_owner, self.group.id, False)

        with self.assertRaises(PermissionDenied):
            hydroshare.set_group_active_status(self.lisa_not_group_owner, self.group.id, True)
