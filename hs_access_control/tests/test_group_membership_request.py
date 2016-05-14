from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.models import PrivilegeCodes
#from hs_access_control.tests.utilities import global_reset


class GroupMembershipRequest(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(GroupMembershipRequest, self).setUp()
        #global_reset()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='administrator',
            last_name='dash',
            superuser=True,
            groups=[]
        )

        self.john_group_owner = hydroshare.create_account(
            'jhon@gmail.com',
            username='jharvey',
            first_name='John',
            last_name='Harvey',
            superuser=False,
            groups=[]
        )
        self.mike_group_owner = hydroshare.create_account(
            'mike@gmail.com',
            username='mholley',
            first_name='Mike',
            last_name='Holley',
            superuser=False,
            groups=[]
        )
        self.jen_group_editor = hydroshare.create_account(
            'jen@gmail.com',
            username='jlarson',
            first_name='Jen',
            last_name='Larson',
            superuser=False,
            groups=[]
        )

        self.kim_group_viewer = hydroshare.create_account(
            'kim@gmail.com',
            username='kjordan',
            first_name='Kim',
            last_name='Jordan',
            superuser=False,
            groups=[]
        )

        self.lisa_group_member = hydroshare.create_account(
            'lisa@gmail.com',
            username='lkelly',
            first_name='Lisa',
            last_name='Kelly',
            superuser=False,
            groups=[]
        )

        self.modeling_group = self.john_group_owner.uaccess.create_group(
            title='USU Modeling Group',
            description="We are the cool modeling group",
            purpose="Our purpose to collaborate on hydrologic modeling")

        self.john_group_owner.uaccess.share_group_with_user(self.modeling_group, self.mike_group_owner,
                                                            PrivilegeCodes.OWNER)
        self.john_group_owner.uaccess.share_group_with_user(self.modeling_group, self.jen_group_editor,
                                                            PrivilegeCodes.CHANGE)
        self.john_group_owner.uaccess.share_group_with_user(self.modeling_group, self.kim_group_viewer,
                                                            PrivilegeCodes.VIEW)

    def test_owner_sending_invitation(self):
        # group owner should have no pending invitations to join group
        self.assertEquals(self.john_group_owner.uaccess.group_membership_requests.count(), 0)

        # modeling group should have no pending membership requests
        self.assertEquals(self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # there should be 4 members in the group
        self.assertEquals(self.modeling_group.gaccess.members.count(), 4)

        # let the group owner (john) send a membership invitation to user lisa
        membership_request = self.john_group_owner.uaccess.create_group_membership_request(self.modeling_group,
                                                                                           self.lisa_group_member)

        # test that inviting the same user more than once should raise exception
        # let the group owner (john) send a membership invitation to user lisa again
        with self.assertRaises(PermissionDenied):
            self.john_group_owner.uaccess.create_group_membership_request(self.modeling_group,
                                                                          self.lisa_group_member)

        # group owner should have one pending invitations to join group
        self.assertEquals(self.john_group_owner.uaccess.group_membership_requests.count(), 1)

        # modeling group should have one pending membership requests
        self.assertEquals(self.modeling_group.gaccess.group_membership_requests.count(), 1)

        # let lisa accept the invitation to join modeling group
        self.lisa_group_member.uaccess.act_on_group_membership_request(membership_request, accept_request=True)

        # there should be 5 members in the group
        self.assertEquals(self.modeling_group.gaccess.members.count(), 5)
        # lisa should be one of the members
        self.assertIn(self.lisa_group_member, self.modeling_group.gaccess.members)

        # group owner should have no pending invitations to join group
        self.assertEquals(self.john_group_owner.uaccess.group_membership_requests.count(), 0)

        # modeling group should have no pending membership requests
        self.assertEquals(self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # sending invitation to an user who is already a member should raise exception
        # let the group owner (john) send a membership invitation to user lisa who is already a member
        with self.assertRaises(PermissionDenied):
            self.john_group_owner.uaccess.create_group_membership_request(self.modeling_group,
                                                                          self.lisa_group_member)

        # remove lisa from the modeling group
        self.john_group_owner.uaccess.undo_share_group_with_user(self.modeling_group, self.lisa_group_member)
        # there should be 4 members in the group
        self.assertEquals(self.modeling_group.gaccess.members.count(), 4)

        # let the group owner (john) send a membership invitation to user lisa
        membership_request = self.john_group_owner.uaccess.create_group_membership_request(self.modeling_group,
                                                                                           self.lisa_group_member)
        # let lisa decline the invitation to join modeling group
        self.lisa_group_member.uaccess.act_on_group_membership_request(membership_request, accept_request=False)

        # there should be 4 members in the group
        self.assertEquals(self.modeling_group.gaccess.members.count(), 4)

        # group owner should have no pending invitations to join group
        self.assertEquals(self.john_group_owner.uaccess.group_membership_requests.count(), 0)

        # modeling group should have no pending membership requests
        self.assertEquals(self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # TODO: Test multiple owners inviting different users to join a specific group

    def test_non_owner_sending_invitation(self):
        # test group non-owners can't send invitation to users to join group
        with self.assertRaises(PermissionDenied):
            self.jen_group_editor.uaccess.create_group_membership_request(self.modeling_group,
                                                                          self.lisa_group_member)
        with self.assertRaises(PermissionDenied):
            self.kim_group_viewer.uaccess.create_group_membership_request(self.modeling_group,
                                                                          self.lisa_group_member)

    def test_user_sending_request(self):
        # user lisa should have no pending request to join group
        self.assertEquals(self.lisa_group_member.uaccess.group_membership_requests.count(), 0)

        # modeling group should have no pending membership requests
        self.assertEquals(self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # there should be 4 members in the group
        self.assertEquals(self.modeling_group.gaccess.members.count(), 4)

        # let lisa send a membership request to join modeling group
        membership_request = self.lisa_group_member.uaccess.create_group_membership_request(self.modeling_group)

        # modeling group should have one pending membership requests
        self.assertEquals(self.modeling_group.gaccess.group_membership_requests.count(), 1)

        # trying to send multiple request to join the same group should raise exception
        with self.assertRaises(PermissionDenied):
            self.lisa_group_member.uaccess.create_group_membership_request(self.modeling_group)

        # user lisa should have 1 pending request to join group
        self.assertEquals(self.lisa_group_member.uaccess.group_membership_requests.count(), 1)

        # modeling group should have 1 pending membership requests
        self.assertEquals(self.modeling_group.gaccess.group_membership_requests.count(), 1)

        # there should be 4 members in the group
        self.assertEquals(self.modeling_group.gaccess.members.count(), 4)

        # let john (group owner) accept lisa's request
        self.john_group_owner.uaccess.act_on_group_membership_request(membership_request, accept_request=True)

        # user lisa should have no pending request to join group
        self.assertEquals(self.lisa_group_member.uaccess.group_membership_requests.count(), 0)
        # modeling group should have no pending membership requests
        self.assertEquals(self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # there should be 5 members in the group
        self.assertEquals(self.modeling_group.gaccess.members.count(), 5)
        # lisa should be one of the members
        self.assertIn(self.lisa_group_member, self.modeling_group.gaccess.members)

        # trying to send request to join a group in which you are already a member should raise exception
        with self.assertRaises(PermissionDenied):
            self.lisa_group_member.uaccess.create_group_membership_request(self.modeling_group)

        # remove lisa from the modeling group
        self.john_group_owner.uaccess.undo_share_group_with_user(self.modeling_group, self.lisa_group_member)

        # let lisa send a membership request to join modeling group
        membership_request = self.lisa_group_member.uaccess.create_group_membership_request(self.modeling_group)
        # let john (group owner) decline lisa's request
        self.john_group_owner.uaccess.act_on_group_membership_request(membership_request, accept_request=False)
        # there should be 4 members in the group
        self.assertEquals(self.modeling_group.gaccess.members.count(), 4)
        # user lisa should have no pending request to join group
        self.assertEquals(self.lisa_group_member.uaccess.group_membership_requests.count(), 0)

        # modeling group should have no pending membership requests
        self.assertEquals(self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # test user cancelling his/her own request to join a group
        # let lisa send a membership request to join modeling group
        membership_request = self.lisa_group_member.uaccess.create_group_membership_request(self.modeling_group)
        # user lisa should have 1 pending request to join group
        self.assertEquals(self.lisa_group_member.uaccess.group_membership_requests.count(), 1)
        # modeling group should have 1 pending membership requests
        self.assertEquals(self.modeling_group.gaccess.group_membership_requests.count(), 1)
        # let Lisa cancel her own request to join group
        self.lisa_group_member.uaccess.act_on_group_membership_request(membership_request, accept_request=False)
        # user lisa should have no pending request to join group
        self.assertEquals(self.lisa_group_member.uaccess.group_membership_requests.count(), 0)
        # modeling group should have no pending membership requests
        self.assertEquals(self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # TODO: Test multiple users making requests to join the same group

    def test_non_owners_acting_on_requests(self):
        # test a request to join a group can't be accepted or declined by group non-owners
        # let lisa send a membership request to join modeling group
        membership_request = self.lisa_group_member.uaccess.create_group_membership_request(self.modeling_group)
        with self.assertRaises(PermissionDenied):
            self.jen_group_editor.uaccess.act_on_group_membership_request(membership_request, accept_request=True)

        with self.assertRaises(PermissionDenied):
            self.kim_group_viewer.uaccess.act_on_group_membership_request(membership_request, accept_request=True)

        with self.assertRaises(PermissionDenied):
            self.jen_group_editor.uaccess.act_on_group_membership_request(membership_request, accept_request=False)

        with self.assertRaises(PermissionDenied):
            self.kim_group_viewer.uaccess.act_on_group_membership_request(membership_request, accept_request=False)


