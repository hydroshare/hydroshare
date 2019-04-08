from django.test import TestCase
from django.contrib.auth.models import Group

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.models import PrivilegeCodes
from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set


class T11ExplicitGet(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(T11ExplicitGet, self).setUp()
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
            resource_type='GenericResource', owner=self.A_user, title='R1', metadata=[],)

        self.r2_resource = hydroshare.create_resource(
            resource_type='GenericResource', owner=self.A_user, title='R2', metadata=[],)

        self.r3_resource = hydroshare.create_resource(
            resource_type='GenericResource', owner=self.A_user, title='R3', metadata=[],)

        self.A_group = self.A_user.uaccess\
            .create_group(title='Test Group A',
                          description="This group is all about testing")

        self.B_group = self.B_user.uaccess\
            .create_group(title='Test Group B',
                          description="This group is all about testing")

        self.C_group = self.C_user.uaccess\
            .create_group(title='Test Group C',
                          description="This group is all about testing")

    def test_01_user_level_access(self):
        "Test all options for user-level access (the default)"
        A_user = self.A_user
        B_user = self.B_user
        C_user = self.C_user
        r1_resource = self.r1_resource
        r2_resource = self.r2_resource
        r3_resource = self.r3_resource

        A_user.uaccess.share_resource_with_user(
            r1_resource, C_user, PrivilegeCodes.OWNER)
        A_user.uaccess.share_resource_with_user(
            r2_resource, C_user, PrivilegeCodes.OWNER)
        A_user.uaccess.share_resource_with_user(
            r3_resource, C_user, PrivilegeCodes.OWNER)

        foo = A_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.OWNER)
        self.assertTrue(
            is_equal_to_as_set(
                foo, [r1_resource, r2_resource, r3_resource]))
        foo = A_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(foo, []))
        foo = A_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(foo, []))
        foo = C_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.OWNER)
        self.assertTrue(
            is_equal_to_as_set(
                foo, [r1_resource, r2_resource, r3_resource]))
        foo = C_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(foo, []))
        foo = C_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(foo, []))

        A_user.uaccess.share_resource_with_user(
            r1_resource, B_user, PrivilegeCodes.OWNER)
        A_user.uaccess.share_resource_with_user(
            r2_resource, B_user, PrivilegeCodes.CHANGE)
        A_user.uaccess.share_resource_with_user(
            r3_resource, B_user, PrivilegeCodes.VIEW)

        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(foo, [r1_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(foo, [r2_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(foo, [r3_resource]))

        # higher privileges are deleted when lower privileges are granted
        C_user.uaccess.share_resource_with_user(
            r1_resource, B_user, PrivilegeCodes.VIEW)
        C_user.uaccess.share_resource_with_user(
            r2_resource, B_user, PrivilegeCodes.VIEW)

        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(foo, []))    # [r1_resource]
        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(foo, []))    # [r2_resource]
        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                foo, [r1_resource, r2_resource, r3_resource]))

        C_user.uaccess.share_resource_with_user(
            r1_resource, B_user, PrivilegeCodes.CHANGE)
        C_user.uaccess.share_resource_with_user(
            r2_resource, B_user, PrivilegeCodes.CHANGE)
        C_user.uaccess.share_resource_with_user(
            r3_resource, B_user, PrivilegeCodes.CHANGE)

        # higher privilege gets deleted when a lower privilege is granted
        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(foo, []))    # [r1_resource]
        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.CHANGE)
        self.assertTrue(
            is_equal_to_as_set(
                foo, [r1_resource, r2_resource, r3_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(foo, []))

        # go from lower privilege to higher
        C_user.uaccess.share_resource_with_user(
            r1_resource, B_user, PrivilegeCodes.VIEW)
        C_user.uaccess.share_resource_with_user(
            r2_resource, B_user, PrivilegeCodes.VIEW)
        C_user.uaccess.share_resource_with_user(
            r3_resource, B_user, PrivilegeCodes.VIEW)

        A_user.uaccess.share_resource_with_user(
            r1_resource, B_user, PrivilegeCodes.CHANGE)
        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(foo, [r1_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(foo, [r2_resource, r3_resource]))

        A_user.uaccess.share_resource_with_user(
            r1_resource, B_user, PrivilegeCodes.OWNER)

        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(foo, [r1_resource]))
        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(foo, [r2_resource, r3_resource]))

        # go lower to higher
        C_user.uaccess.share_resource_with_user(
            r1_resource, B_user, PrivilegeCodes.VIEW)

        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.OWNER)
        self.assertTrue(is_equal_to_as_set(foo, []))
        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(foo, []))
        foo = B_user.uaccess.get_resources_with_explicit_access(
            PrivilegeCodes.VIEW)
        self.assertTrue(
            is_equal_to_as_set(
                foo, [r1_resource, r2_resource, r3_resource]))

    def test_02_group_level_access(self):

        A_user = self.A_user
        B_user = self.B_user
        A_group = self.A_group
        B_group = self.B_group
        r1_resource = self.r1_resource
        r2_resource = self.r2_resource
        r3_resource = self.r3_resource

        # A owns everything
        g = A_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER,
                                                              via_user=True,
                                                              via_group=False)
        self.assertTrue(is_equal_to_as_set(g, [r1_resource, r2_resource, r3_resource]))

        g = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                              via_user=False,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, []))

        A_user.uaccess.share_resource_with_group(r1_resource, A_group, PrivilegeCodes.CHANGE)

        g = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                              via_user=False,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, []))

        A_user.uaccess.share_group_with_user(A_group, B_user, PrivilegeCodes.CHANGE)

        g = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                              via_user=False,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, [r1_resource]))

        # no user owned resources
        g = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                              via_user=True,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, [r1_resource]))

        # mixed dominance relationships:
        # in situations where there is a higher privilege,
        # lower privilege should be eliminated, even if from a different source

        B_user.uaccess.share_resource_with_group(r1_resource, B_group, PrivilegeCodes.CHANGE)
        A_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.OWNER)
        g = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER,
                                                              via_user=True,
                                                              via_group=True)
        # should be OWNER now
        self.assertTrue(is_equal_to_as_set(g, [r1_resource]))

        # OWNER squashes CHANGE
        g = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                              via_user=True,
                                                              via_group=True)

        self.assertTrue(is_equal_to_as_set(g, []))

        # OWNER squashes VIEW
        g = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW,
                                                              via_user=True,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, []))

    def test_03_immutability(self):

        A_user = self.A_user
        B_user = self.B_user
        C_user = self.C_user
        B_group = self.B_group
        r1_resource = self.r1_resource
        r2_resource = self.r2_resource
        r3_resource = self.r3_resource

        # A owns everything
        g = A_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER,
                                                              via_user=True,
                                                              via_group=False)
        self.assertTrue(is_equal_to_as_set(g, [r1_resource, r2_resource, r3_resource]))

        # grant change access via user
        A_user.uaccess.share_resource_with_user(r1_resource, B_user, PrivilegeCodes.CHANGE)
        B_user.uaccess.share_resource_with_group(r1_resource, B_group, PrivilegeCodes.CHANGE)
        B_user.uaccess.share_group_with_user(B_group, C_user, PrivilegeCodes.VIEW)

        # B_user's CHANGE should be present
        g = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER,
                                                              via_user=True,
                                                              via_group=False)
        self.assertTrue(is_equal_to_as_set(g, []))
        g = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                              via_user=True,
                                                              via_group=False)
        self.assertTrue(is_equal_to_as_set(g, [r1_resource]))
        g = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW,
                                                              via_user=True,
                                                              via_group=False)
        self.assertTrue(is_equal_to_as_set(g, []))

        # C_user's CHANGE should not be present for user
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER,
                                                              via_user=True,
                                                              via_group=False)
        self.assertTrue(is_equal_to_as_set(g, []))
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                              via_user=True,
                                                              via_group=False)
        self.assertTrue(is_equal_to_as_set(g, []))
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW,
                                                              via_user=True,
                                                              via_group=False)
        self.assertTrue(is_equal_to_as_set(g, []))

        # C_user's CHANGE should be present only for group
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER,
                                                              via_user=False,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, []))
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                              via_user=False,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, [r1_resource]))
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW,
                                                              via_user=False,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, []))

        # now set immutable
        r1_resource.raccess.immutable = True
        r1_resource.raccess.save()

        # immutable should squash CHANGE privilege to VIEW
        g = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER,
                                                              via_user=True,
                                                              via_group=False)
        self.assertTrue(is_equal_to_as_set(g, []))
        g = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                              via_user=True,
                                                              via_group=False)
        self.assertTrue(is_equal_to_as_set(g, []))
        g = B_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW,
                                                              via_user=True,
                                                              via_group=False)
        self.assertTrue(is_equal_to_as_set(g, [r1_resource]))

        # C_user's CHANGE should be squashed to VIEW
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER,
                                                              via_user=False,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, []))
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                              via_user=False,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, []))
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW,
                                                              via_user=False,
                                                              via_group=True)

        self.assertTrue(is_equal_to_as_set(g, [r1_resource]))

        # owner squashes CHANGE + immutable
        A_user.uaccess.share_resource_with_user(r1_resource, C_user, PrivilegeCodes.OWNER)

        # when accounting for user privileges,
        # C_user's OWNER should not be squashed to VIEW
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER,
                                                              via_user=True,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, [r1_resource]))
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                              via_user=True,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, []))
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW,
                                                              via_user=True,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, []))

        # but not accounting for users should leave it alone
        # C_user's OWNER should be ignored and squashed to VIEW
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER,
                                                              via_user=False,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, []))
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                              via_user=False,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, []))
        g = C_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW,
                                                              via_user=False,
                                                              via_group=True)
        self.assertTrue(is_equal_to_as_set(g, []))
