from django.test import TestCase
from django.contrib.auth.models import Group

from hs_core import hydroshare

from hs_access_control.models import PrivilegeCodes, shortcut
from hs_access_control.tests.utilities import global_reset


class TestShortcut(TestCase):

    def setUp(self):
        super(TestShortcut, self).setUp()
        global_reset()

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.A_user = hydroshare.create_account(
            'a_user@gmail.com',
            username='A',
            first_name='A First',
            last_name='A Last',
            superuser=False,
            groups=[]
        )

        self.B_user = hydroshare.create_account(
            'b_user@gmail.com',
            username='B',
            first_name='B First',
            last_name='B Last',
            superuser=False,
            groups=[]
        )

        self.C_user = hydroshare.create_account(
            'c_user@gmail.com',
            username='C',
            first_name='C First',
            last_name='C Last',
            superuser=False,
            groups=[]
        )

        self.r1_resource = hydroshare.create_resource(
            resource_type='CompositeResource', owner=self.A_user, title='R1', metadata=[],)

        self.r2_resource = hydroshare.create_resource(
            resource_type='CompositeResource', owner=self.B_user, title='R2', metadata=[],)

        self.r3_resource = hydroshare.create_resource(
            resource_type='CompositeResource', owner=self.C_user, title='R3', metadata=[],)

        self.A_group = self.A_user.uaccess\
            .create_group(title='Test Group A',
                          description="This group is all about testing")

        self.B_group = self.B_user.uaccess\
            .create_group(title='Test Group B',
                          description="This group is all about testing")

        self.C_group = self.C_user.uaccess\
            .create_group(title='Test Group C',
                          description="This group is all about testing")

    def test_01_user_owner_access(self):
        " user has owner access "
        A_user = self.A_user
        B_user = self.B_user
        r1_resource = self.r1_resource
        r2_resource = self.r2_resource

        A_user.uaccess.share_resource_with_user(
            r1_resource, A_user, PrivilegeCodes.OWNER)

        privilege = shortcut.get_user_resource_privilege(A_user.email, r1_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.OWNER)
        privilege = shortcut.get_user_resource_privilege(B_user.email, r1_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.NONE)

        privilege = shortcut.get_user_resource_privilege(A_user.email, r2_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.NONE)

    def test_01_user_change_access(self):
        " user has change access "
        A_user = self.A_user
        B_user = self.B_user
        r2_resource = self.r2_resource

        privilege = shortcut.get_user_resource_privilege(A_user.email, r2_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.NONE)

        B_user.uaccess.share_resource_with_user(
            r2_resource, A_user, PrivilegeCodes.CHANGE)

        privilege = shortcut.get_user_resource_privilege(A_user.email, r2_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.CHANGE)

    def test_01_user_view_access(self):
        " user has view access "
        A_user = self.A_user
        B_user = self.B_user
        r1_resource = self.r1_resource

        privilege = shortcut.get_user_resource_privilege(B_user.email, r1_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.NONE)

        A_user.uaccess.share_resource_with_user(
            r1_resource, B_user, PrivilegeCodes.VIEW)

        privilege = shortcut.get_user_resource_privilege(B_user.email, r1_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.VIEW)

    def test_02_public_access(self):
        " public access gives view access "
        A_user = self.A_user
        r2_resource = self.r2_resource
        r3_resource = self.r3_resource
        r2_resource.raccess.public = True
        r2_resource.raccess.discoverable = True
        r2_resource.raccess.save()

        privilege = shortcut.get_user_resource_privilege(A_user.email, r2_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.VIEW)

        privilege = shortcut.get_user_resource_privilege(A_user.email, r3_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.NONE)

    def test_03_group_view_access(self):
        " group allows view access "
        A_user = self.A_user
        B_user = self.B_user
        A_group = self.A_group
        r1_resource = self.r1_resource

        privilege = shortcut.get_user_resource_privilege(B_user.email, r1_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.NONE)

        A_user.uaccess.share_group_with_user(A_group, B_user, PrivilegeCodes.VIEW)
        A_user.uaccess.share_resource_with_group(r1_resource, A_group, PrivilegeCodes.VIEW)

        privilege = shortcut.get_user_resource_privilege(B_user.email, r1_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.VIEW)

    def test_03_group_change_access(self):
        " group allows change access "
        A_user = self.A_user
        B_user = self.B_user
        A_group = self.A_group
        r1_resource = self.r1_resource

        privilege = shortcut.get_user_resource_privilege(B_user.email, r1_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.NONE)

        A_user.uaccess.share_group_with_user(A_group, B_user, PrivilegeCodes.VIEW)
        A_user.uaccess.share_resource_with_group(r1_resource, A_group, PrivilegeCodes.CHANGE)

        privilege = shortcut.get_user_resource_privilege(B_user.email, r1_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.CHANGE)

    def test_04_crosstalk(self):
        " minimum privilege is returned "

        A_user = self.A_user
        B_user = self.B_user
        A_group = self.A_group
        r1_resource = self.r1_resource

        privilege = shortcut.get_user_resource_privilege(B_user.email, r1_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.NONE)

        A_user.uaccess.share_resource_with_user(
            r1_resource, B_user, PrivilegeCodes.VIEW)

        privilege = shortcut.get_user_resource_privilege(B_user.email, r1_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.VIEW)

        A_user.uaccess.share_group_with_user(A_group, B_user, PrivilegeCodes.VIEW)
        A_user.uaccess.share_resource_with_group(r1_resource, A_group, PrivilegeCodes.CHANGE)
        privilege = shortcut.get_user_resource_privilege(B_user.email, r1_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.CHANGE)

        A_user.uaccess.share_resource_with_user(
            r1_resource, B_user, PrivilegeCodes.OWNER)

        privilege = shortcut.get_user_resource_privilege(B_user.email, r1_resource.short_id)
        self.assertEqual(privilege, PrivilegeCodes.OWNER)
