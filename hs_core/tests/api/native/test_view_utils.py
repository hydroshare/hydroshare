from django.contrib.auth.models import Group
from django.test import TestCase


from hs_core.views.utils import get_resource_edit_users, get_resource_view_users
from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin
from hs_access_control.models import PrivilegeCodes


class TestViewUtils(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestViewUtils, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.john = hydroshare.create_account(
            'john@gmail.com',
            username='john',
            first_name='John',
            last_name='Peterson',
            superuser=False,
            groups=[]
        )

        self.mike = hydroshare.create_account(
            'mike@gmail.com',
            username='mike',
            first_name='Michael',
            last_name='Jonson',
            superuser=False,
            groups=[]
        )

        self.lisa = hydroshare.create_account(
            'lisa@gmail.com',
            username='lisa',
            first_name='Lisa',
            last_name='Ketty',
            superuser=False,
            groups=[]
        )

        # create a resource for sharing with group
        self.resource = hydroshare.create_resource(resource_type='GenericResource',
                                                   owner=self.john,
                                                   title='Test Resource',
                                                   metadata=[]
                                                   )

        self.test_group = self.john.uaccess.create_group(title='Test Group', description="This is a cool group")

    def test_resource_edit_users(self):
        # here we are testing get_resource_edit_users()

        # there should not be any edit users at this point
        self.assertEqual(len(get_resource_edit_users(self.resource)), 0)

        # make mike a member of the test_group
        self.john.uaccess.share_group_with_user(self.test_group, self.mike, PrivilegeCodes.CHANGE)

        # share resource with test group
        self.john.uaccess.share_resource_with_group(self.resource, self.test_group, PrivilegeCodes.CHANGE)

        # there should not be any edit users at this point if we don't include user access to resource via group
        self.assertEqual(len(get_resource_edit_users(self.resource)), 0)

        # there should be one edit users at this point if we include user access to resource via group
        self.assertEqual(len(get_resource_edit_users(self.resource, include_access_via_group=True)), 1)

        # share resource with lisa
        self.john.uaccess.share_resource_with_user(self.resource, self.lisa, PrivilegeCodes.CHANGE)

        # there should be one edit user (lisa) at this point if we don't include user access to resource via group
        self.assertEqual(len(get_resource_edit_users(self.resource)), 1)

        # there should be 2 edit users at this point if we include user access to resource via group
        self.assertEqual(len(get_resource_edit_users(self.resource, include_access_via_group=True)), 2)

    def test_resource_view_users(self):
        # here we are testing get_resource_view_users()

        # there should not be any view users at this point
        self.assertEqual(len(get_resource_view_users(self.resource)), 0)

        # make mike a member of the test_group
        self.john.uaccess.share_group_with_user(self.test_group, self.mike, PrivilegeCodes.VIEW)

        # share resource with test group
        self.john.uaccess.share_resource_with_group(self.resource, self.test_group, PrivilegeCodes.VIEW)

        # there should not be any view users at this point if we don't include user access to resource via group
        self.assertEqual(len(get_resource_view_users(self.resource)), 0)

        # there should be one view users at this point if we include user access to resource via group
        self.assertEqual(len(get_resource_view_users(self.resource, include_access_via_group=True)), 1)

        # share resource with lisa
        self.john.uaccess.share_resource_with_user(self.resource, self.lisa, PrivilegeCodes.VIEW)

        # there should be one view user (lisa) at this point if we don't include user access to resource via group
        self.assertEqual(len(get_resource_view_users(self.resource)), 1)

        # there should be 2 view users at this point if we include user access to resource via group
        self.assertEqual(len(get_resource_view_users(self.resource, include_access_via_group=True)), 2)