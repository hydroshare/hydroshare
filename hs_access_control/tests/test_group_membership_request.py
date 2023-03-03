from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.models import PrivilegeCodes


class GroupMembershipRequest(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(GroupMembershipRequest, self).setUp()
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
            username='lisa',
            first_name='Lisa',
            last_name='Larson',
            superuser=False,
            groups=[]
        )

        self.kelly_group_member = hydroshare.create_account(
            'kelly@gmail.com',
            username='kelly',
            first_name='Kelly',
            last_name='Miller',
            superuser=False,
            groups=[]
        )

        self.modeling_group = self.john_group_owner.uaccess.create_group(
            title='USU Modeling Group',
            description="We are the cool modeling group",
            purpose="Our purpose to collaborate on hydrologic modeling")

        self.metadata_group = self.mike_group_owner.uaccess.create_group(
            title='USU Metadata Group',
            description="We are the cool metadata group",
            purpose="Our purpose to collaborate on metadata")

        self.john_group_owner.uaccess.share_group_with_user(
            self.modeling_group, self.mike_group_owner, PrivilegeCodes.OWNER)
        self.john_group_owner.uaccess.share_group_with_user(
            self.modeling_group, self.jen_group_editor, PrivilegeCodes.CHANGE)
        self.john_group_owner.uaccess.share_group_with_user(
            self.modeling_group, self.kim_group_viewer, PrivilegeCodes.VIEW)

    def test_owner_sending_invitation(self):
        # group owner should have no pending invitations to join group
        self.assertEqual(
            self.john_group_owner.uaccess.group_membership_requests.count(), 0)
        self.assertEqual(
            self.mike_group_owner.uaccess.group_membership_requests.count(), 0)

        # modeling group should have no pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # there should be 4 members in the modeling group
        self.assertEqual(self.modeling_group.gaccess.members.count(), 4)

        # let the group owner (john) send a membership invitation to user lisa
        membership_request = self.john_group_owner.uaccess.create_group_membership_request(
            self.modeling_group, self.lisa_group_member)

        # test that inviting the same user more than once should raise exception
        # let the group owner (john) send a membership invitation to user lisa
        # again
        with self.assertRaises(PermissionDenied):
            self.john_group_owner.uaccess.create_group_membership_request(
                self.modeling_group, self.lisa_group_member)

        # let the group owner (mike) send a membership invitation to user lisa
        # again
        with self.assertRaises(PermissionDenied):
            self.mike_group_owner.uaccess.create_group_membership_request(
                self.modeling_group, self.lisa_group_member)

        # group owner john should have one pending invitations to join group
        self.assertEqual(
            self.john_group_owner.uaccess.group_membership_requests.count(), 1)
        # group owner mike should have no pending invitations to join group
        self.assertEqual(
            self.mike_group_owner.uaccess.group_membership_requests.count(), 0)

        # modeling group should have one pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 1)

        # let lisa accept the invitation to join modeling group
        self.lisa_group_member.uaccess.act_on_group_membership_request(
            membership_request, accept_request=True)

        # there should be 5 members in the group
        self.assertEqual(self.modeling_group.gaccess.members.count(), 5)
        # lisa should be one of the members
        self.assertIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)

        # group owner should have no pending invitations to join group
        self.assertEqual(
            self.john_group_owner.uaccess.group_membership_requests.count(), 0)
        self.assertEqual(
            self.mike_group_owner.uaccess.group_membership_requests.count(), 0)

        # modeling group should have no pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # sending invitation to an user who is already a member should raise exception
        # let the group owner (john) send a membership invitation to user lisa
        # who is already a member
        with self.assertRaises(PermissionDenied):
            self.john_group_owner.uaccess.create_group_membership_request(
                self.modeling_group, self.lisa_group_member)

        # let the group owner (mike) send a membership invitation to user lisa
        # who is already a member
        with self.assertRaises(PermissionDenied):
            self.mike_group_owner.uaccess.create_group_membership_request(
                self.modeling_group, self.lisa_group_member)

        # remove lisa from the modeling group
        self.john_group_owner.uaccess.unshare_group_with_user(
            self.modeling_group, self.lisa_group_member)
        # there should be now 4 members in the group
        self.assertEqual(self.modeling_group.gaccess.members.count(), 4)

        # let the group owner (mike) send a membership invitation to user lisa
        membership_request = self.mike_group_owner.uaccess.create_group_membership_request(
            self.modeling_group, self.lisa_group_member)
        # let lisa decline the invitation to join modeling group
        self.lisa_group_member.uaccess.act_on_group_membership_request(
            membership_request, accept_request=False)

        # lisa should not be one of the members
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)

        # there should be now 4 members in the group
        self.assertEqual(self.modeling_group.gaccess.members.count(), 4)

        # group owner should have no pending invitations to join group
        self.assertEqual(
            self.mike_group_owner.uaccess.group_membership_requests.count(), 0)

        # modeling group should have no pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # test group owner cancelling invitation

        # let john (group owner) invite lisa to join group
        membership_request = self.john_group_owner.uaccess.create_group_membership_request(
            self.modeling_group, self.lisa_group_member)
        # let john cancel his own invitation
        self.john_group_owner.uaccess.act_on_group_membership_request(
            membership_request, accept_request=False)

        # let john (group owner) invite lisa to join group
        membership_request = self.john_group_owner.uaccess.create_group_membership_request(
            self.modeling_group, self.lisa_group_member)
        # let mike (group owner) cancel john's invitation to lisa
        self.mike_group_owner.uaccess.act_on_group_membership_request(
            membership_request, accept_request=False)

    def test_owner_inviting_same_user_different_groups(self):
        # lisa should not be one of the members of the modeling group
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)
        # lisa should not be one of the members of the metadata group
        self.assertNotIn(
            self.lisa_group_member,
            self.metadata_group.gaccess.members)

        # let the metadata group owner (mike) send a membership invitation to
        # user lisa
        metadata_membership_request = \
            self.mike_group_owner.uaccess.create_group_membership_request(self.metadata_group,
                                                                          self.lisa_group_member)
        # let the modeling group owner (mike) send a membership invitation to
        # user lisa
        modeling_membership_request = self.mike_group_owner.uaccess.create_group_membership_request(
            self.modeling_group, self.lisa_group_member)

        # let lisa accept both invitations
        self.lisa_group_member.uaccess.act_on_group_membership_request(
            metadata_membership_request, accept_request=True)
        self.lisa_group_member.uaccess.act_on_group_membership_request(
            modeling_membership_request, accept_request=True)
        # lisa should be one of the members of the modeling group
        self.assertIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)
        # lisa should be one of the members of the metadata group
        self.assertIn(
            self.lisa_group_member,
            self.metadata_group.gaccess.members)

    def test_non_owner_sending_invitation(self):
        # test group non-owners can't send invitation to users to join group
        with self.assertRaises(PermissionDenied):
            self.jen_group_editor.uaccess.create_group_membership_request(
                self.modeling_group, self.lisa_group_member)
        with self.assertRaises(PermissionDenied):
            self.kim_group_viewer.uaccess.create_group_membership_request(
                self.modeling_group, self.lisa_group_member)

    def test_user_sending_request(self):
        # user lisa should have no pending request to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 0)

        # modeling group should have no pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # there should be 4 members in the group
        self.assertEqual(self.modeling_group.gaccess.members.count(), 4)

        # lisa should should not be one of the members
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)

        # let lisa send a membership request to join modeling group
        membership_request = self.lisa_group_member.uaccess.create_group_membership_request(
            self.modeling_group)

        # modeling group should have one pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 1)

        # same user trying to send multiple request to join the same group
        # should raise exception
        with self.assertRaises(PermissionDenied):
            self.lisa_group_member.uaccess.create_group_membership_request(
                self.modeling_group)

        # user lisa should have 1 pending request to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 1)

        # modeling group should have 1 pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 1)

        # there should be 4 members in the group
        self.assertEqual(self.modeling_group.gaccess.members.count(), 4)

        # let john (group owner) accept lisa's request
        self.john_group_owner.uaccess.act_on_group_membership_request(
            membership_request, accept_request=True)

        # user lisa should have no pending request to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 0)
        # modeling group should have no pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # there should be 5 members in the group
        self.assertEqual(self.modeling_group.gaccess.members.count(), 5)
        # lisa should be one of the members
        self.assertIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)

        # user trying to send request to join a group in which he/she is
        # already a member should raise exception
        with self.assertRaises(PermissionDenied):
            self.lisa_group_member.uaccess.create_group_membership_request(
                self.modeling_group)

        # let group owner mike remove lisa from the modeling group
        self.mike_group_owner.uaccess.unshare_group_with_user(
            self.modeling_group, self.lisa_group_member)
        # lisa should not be one of the members
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)

        # let lisa send a membership request to join modeling group
        membership_request = self.lisa_group_member.uaccess.create_group_membership_request(
            self.modeling_group)
        # let john (group owner) decline lisa's request
        self.john_group_owner.uaccess.act_on_group_membership_request(
            membership_request, accept_request=False)
        # there should be 4 members in the group
        self.assertEqual(self.modeling_group.gaccess.members.count(), 4)
        # lisa should not be one of the members
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)
        # user lisa should have no pending request to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 0)
        # modeling group should have no pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # test user cancelling his/her own request to join a group
        # let lisa send a membership request to join modeling group
        membership_request = self.lisa_group_member.uaccess.create_group_membership_request(
            self.modeling_group)
        # user lisa should have 1 pending request to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 1)
        # modeling group should have 1 pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 1)
        # let Lisa cancel her own request to join group
        self.lisa_group_member.uaccess.act_on_group_membership_request(
            membership_request, accept_request=False)
        # lisa should not be one of the members
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)
        # user lisa should have no pending request to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 0)
        # modeling group should have no pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 0)

    def test_user_sending_request_with_explanation(self):
        # require explanation on the group
        self.modeling_group.gaccess.requires_explanation = True

        # lisa should should not be one of the members
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)

        # let lisa send a membership request to join modeling group without any explanation
        with self.assertRaises(PermissionDenied):
            membership_request = self.lisa_group_member.uaccess.create_group_membership_request(
                self.modeling_group, explanation=None)

        # modeling group should have zero pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # user lisa should have zero requests to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 0)

        # let lisa send a membership request with an explanation
        membership_request = self.lisa_group_member.uaccess.create_group_membership_request(
            self.modeling_group, explanation="I always have to explain myself")

        # modeling group should have one pending membership request
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 1)

        # user lisa should have 1 pending request to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 1)

        # let john (group owner) accept lisa's request
        self.john_group_owner.uaccess.act_on_group_membership_request(
            membership_request, accept_request=True)

        # user lisa should have no pending request to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 0)

        # modeling group should have no pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # let kelly send a membership request to join modeling group that is too long
        long_string = "Sometimes I just start writing and I can not stop. " * 6
        print(long_string)
        with self.assertRaises(PermissionDenied):
            membership_request = self.kelly_group_member.uaccess.create_group_membership_request(
                self.modeling_group, explanation=long_string)

        # let kelly send a membership request to join modeling group that is appropriate length
        membership_request = self.kelly_group_member.uaccess.create_group_membership_request(
            self.modeling_group, explanation="Sometimes I start writing and I am able to stop.")
        # let john (group owner) decline kelly's request
        self.john_group_owner.uaccess.act_on_group_membership_request(
            membership_request, accept_request=False)
        # there should be 5 members in the group
        self.assertEqual(self.modeling_group.gaccess.members.count(), 5)
        # kelly should not be one of the members
        self.assertNotIn(
            self.kelly_group_member,
            self.modeling_group.gaccess.members)
        # user kelly should have no pending request to join group
        self.assertEqual(
            self.kelly_group_member.uaccess.group_membership_requests.count(), 0)
        # modeling group should have no pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 0)

    def test_user_sending_invitation_without_explanation(self):
        # require explanation on the group
        self.modeling_group.gaccess.requires_explanation = True
        self.modeling_group.gaccess.save()

        # lisa should should not be one of the members
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)

        # user lisa should have no pending request to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 0)

        # modeling group should have no pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # there should be 4 members in the group
        self.assertEqual(self.modeling_group.gaccess.members.count(), 4)

        # let john (group owner) invite lisa to join group without explanation
        membership_request = self.john_group_owner.uaccess.create_group_membership_request(
            self.modeling_group, self.lisa_group_member)

        # modeling group should have 1 pending membership request
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 1)

        # user lisa should have 1 request to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 1)

        # let lisa accept john's invitation
        self.lisa_group_member.uaccess.act_on_group_membership_request(
            membership_request, accept_request=True)

        # user lisa should have no pending request to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 0)

        # modeling group should have no pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # there should be 5 members in the group
        self.assertEqual(self.modeling_group.gaccess.members.count(), 5)

    def test_user_sending_request_auto_approval(self):
        # here we are testing auto approval of group membership request

        # test that the modeling group is not set for auto membership approval
        self.assertEqual(self.modeling_group.gaccess.auto_approve, False)

        # user lisa should have no pending request to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 0)

        # modeling group should have no pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # there should be 4 members in the group
        self.assertEqual(self.modeling_group.gaccess.members.count(), 4)

        # lisa should should not be one of the members
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)

        # set the modeling group for auto membership approval
        self.modeling_group.gaccess.auto_approve = True
        self.modeling_group.gaccess.save()

        # let lisa send a membership request to join modeling group - which is an auto
        # membership approval group
        self.lisa_group_member.uaccess.create_group_membership_request(self.modeling_group)

        # user lisa should have no pending request to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 0)
        # modeling group should have no pending membership requests
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 0)

        # lisa should be a member of the modeling group
        self.assertIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)

    def test_user_sending_request_multiple_groups(self):
        # test that a specific user can send request to join multiple groups

        # lisa should not be one of the members of the modeling group
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)
        # lisa should not be one of the members of the metadata group
        self.assertNotIn(
            self.lisa_group_member,
            self.metadata_group.gaccess.members)

        # let lisa make request to join modeling and metadata groups
        modeling_membership_request = \
            self.lisa_group_member.uaccess.create_group_membership_request(self.modeling_group)
        metadata_membership_request = \
            self.lisa_group_member.uaccess.create_group_membership_request(self.metadata_group)

        # let group owner mike accept lisa's requests
        self.mike_group_owner.uaccess.act_on_group_membership_request(
            modeling_membership_request, accept_request=True)
        self.mike_group_owner.uaccess.act_on_group_membership_request(
            metadata_membership_request, accept_request=True)

        # lisa should be one of the members of the modeling group
        self.assertIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)
        # lisa should be one of the members of the metadata group
        self.assertIn(
            self.lisa_group_member,
            self.metadata_group.gaccess.members)

    def test_multiple_user_sending_request(self):
        # test multiple users making requests to join the same group

        # lisa should not be one of the members
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)
        # kelly should not be one of the members
        self.assertNotIn(
            self.kelly_group_member,
            self.modeling_group.gaccess.members)
        # let lisa send a membership request to join modeling group
        lisa_membership_request = self.lisa_group_member.uaccess.create_group_membership_request(
            self.modeling_group)
        # user lisa should have 1 pending request to join group
        self.assertEqual(
            self.lisa_group_member.uaccess.group_membership_requests.count(), 1)
        self.assertIn(lisa_membership_request,
                      self.modeling_group.gaccess.group_membership_requests)
        # let kelly send a membership request to join modeling group
        kelly_membership_request = self.kelly_group_member.uaccess.create_group_membership_request(
            self.modeling_group)
        # user kelly should have 1 pending request to join group
        self.assertEqual(
            self.kelly_group_member.uaccess.group_membership_requests.count(), 1)
        self.assertIn(kelly_membership_request,
                      self.modeling_group.gaccess.group_membership_requests)
        # modeling group should have 2 pending membership requests (one from
        # lisa and one from kelly)
        self.assertEqual(
            self.modeling_group.gaccess.group_membership_requests.count(), 2)
        # let john (group owner) accept lisa's request
        self.john_group_owner.uaccess.act_on_group_membership_request(
            lisa_membership_request, accept_request=True)
        # let mike (group owner) accept kelly's request
        self.mike_group_owner.uaccess.act_on_group_membership_request(
            kelly_membership_request, accept_request=True)
        # there should be 6 members in the group
        self.assertEqual(self.modeling_group.gaccess.members.count(), 6)
        # lisa should be one of the members
        self.assertIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)
        # kelly should be one of the members
        self.assertIn(
            self.kelly_group_member,
            self.modeling_group.gaccess.members)

    def test_group_access_privilege_on_request_acceptance(self):
        # when a request is accepted to join a group, the new member gets VIEW
        # permission only

        # lisa should not be one of the members
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)
        # let the group owner (john) send a membership invitation to user lisa
        membership_request = self.john_group_owner.uaccess.create_group_membership_request(
            self.modeling_group, self.lisa_group_member)
        # let lisa accept the invitation to join modeling group
        self.lisa_group_member.uaccess.act_on_group_membership_request(
            membership_request, accept_request=True)
        # check lisa has view permission on modeling group
        # lisa should be one of the members
        self.assertIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)
        # lisa should not be one of the owners
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.owners)
        # lisa should not be one of the editor
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.edit_users)

        # kelly should not be one of the members
        self.assertNotIn(
            self.kelly_group_member,
            self.modeling_group.gaccess.members)
        # let kelly make a request to join group
        membership_request = self.kelly_group_member.uaccess.create_group_membership_request(
            self.modeling_group)
        # let Mike accept Kelly's request
        self.mike_group_owner.uaccess.act_on_group_membership_request(
            membership_request, accept_request=True)
        # kelly should be one of the members
        self.assertIn(
            self.kelly_group_member,
            self.modeling_group.gaccess.members)
        # kelly should not be one of the owners
        self.assertNotIn(
            self.kelly_group_member,
            self.modeling_group.gaccess.owners)
        # lisa should not be one of the editor
        self.assertNotIn(
            self.kelly_group_member,
            self.modeling_group.gaccess.edit_users)

    def test_non_owners_acting_on_requests(self):
        # test a request to join a group can't be accepted or declined by group non-owners
        # let lisa send a membership request to join modeling group
        membership_request = self.lisa_group_member.uaccess.create_group_membership_request(
            self.modeling_group)
        with self.assertRaises(PermissionDenied):
            self.jen_group_editor.uaccess.act_on_group_membership_request(
                membership_request, accept_request=True)

        with self.assertRaises(PermissionDenied):
            self.kim_group_viewer.uaccess.act_on_group_membership_request(
                membership_request, accept_request=True)

        with self.assertRaises(PermissionDenied):
            self.jen_group_editor.uaccess.act_on_group_membership_request(
                membership_request, accept_request=False)

        with self.assertRaises(PermissionDenied):
            self.kim_group_viewer.uaccess.act_on_group_membership_request(
                membership_request, accept_request=False)

    def test_inactive_user(self):
        # inactive user can't make request to join a group - PermissionDenied
        # exception
        self.lisa_group_member.is_active = False
        self.lisa_group_member.save()
        # lisa should not be one of the members
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)
        with self.assertRaises(PermissionDenied):
            self.lisa_group_member.uaccess.create_group_membership_request(
                self.modeling_group)

        # inactive user can't accept/decline request to join a group -
        # PermissionDenied exception
        self.lisa_group_member.is_active = True
        self.lisa_group_member.save()
        # let the group owner (mike) send a membership invitation to user lisa
        membership_request = self.mike_group_owner.uaccess.create_group_membership_request(
            self.modeling_group, self.lisa_group_member)
        self.lisa_group_member.is_active = False
        self.lisa_group_member.save()
        with self.assertRaises(PermissionDenied):
            self.lisa_group_member.uaccess.act_on_group_membership_request(
                membership_request, accept_request=True)

        with self.assertRaises(PermissionDenied):
            self.lisa_group_member.uaccess.act_on_group_membership_request(
                membership_request, accept_request=False)

        # inactive group owner can't invite user to join a group -
        # PermissionDenied exception
        self.mike_group_owner.is_active = False
        self.mike_group_owner.save()
        self.lisa_group_member.is_active = True
        self.lisa_group_member.save()
        with self.assertRaises(PermissionDenied):
            self.mike_group_owner.uaccess.create_group_membership_request(
                self.modeling_group, self.lisa_group_member)

        # inactive group owner can't accept/decline user request to join a
        # group - PermissionDenied exception
        membership_request = self.lisa_group_member.uaccess.create_group_membership_request(
            self.modeling_group)
        with self.assertRaises(PermissionDenied):
            self.mike_group_owner.uaccess.act_on_group_membership_request(
                membership_request, accept_request=True)
        with self.assertRaises(PermissionDenied):
            self.mike_group_owner.uaccess.act_on_group_membership_request(
                membership_request, accept_request=False)

        # previously existing requests are redeemed if a user is deactivated
        # kelly has no open requests
        self.assertEqual(
            self.kelly_group_member.uaccess.group_membership_requests.count(), 0)

        kelly_membership_request = self.kelly_group_member.uaccess.create_group_membership_request(
            self.modeling_group)
        # user kelly should have pending request to join group
        self.assertIn(kelly_membership_request,
                      self.modeling_group.gaccess.group_membership_requests)
        self.kelly_group_member.is_active = False
        self.kelly_group_member.save()

        # john acts on the existing request
        with self.assertRaises(PermissionDenied):
            self.john_group_owner.uaccess.act_on_group_membership_request(
                kelly_membership_request, accept_request=False)

        # reactivate kelly
        self.kelly_group_member.is_active = True
        self.kelly_group_member.save()

        # Kelly has no active membership requests
        self.assertEqual(
            self.kelly_group_member.uaccess.group_membership_requests.count(), 0)
        self.assertNotIn(kelly_membership_request,
                         self.modeling_group.gaccess.group_membership_requests)

    def test_super_user(self):
        # super user/ admin can send invitation, accept/decline request to join
        # a group

        # super user send invitation to lisa to join group
        # lisa should not be one of the members
        self.assertNotIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)
        membership_request = self.admin.uaccess.create_group_membership_request(
            self.modeling_group, self.lisa_group_member)
        # let lisa accept the invitation
        self.lisa_group_member.uaccess.act_on_group_membership_request(
            membership_request, accept_request=True)
        # lisa should be one of the members
        self.assertIn(
            self.lisa_group_member,
            self.modeling_group.gaccess.members)

        # super user can accept request
        # kelly should not be one of the members
        self.assertNotIn(
            self.kelly_group_member,
            self.modeling_group.gaccess.members)
        # kelly makes request to join group
        membership_request = self.kelly_group_member.uaccess.create_group_membership_request(
            self.modeling_group)
        # let super user accept the request
        self.admin.uaccess.act_on_group_membership_request(
            membership_request, accept_request=True)
        # kelly should be one of the members
        self.assertIn(
            self.kelly_group_member,
            self.modeling_group.gaccess.members)

        # super user can decline request
        # remove kelly from the modeling group
        self.john_group_owner.uaccess.unshare_group_with_user(
            self.modeling_group, self.kelly_group_member)
        # kelly should not be one of the members
        self.assertNotIn(
            self.kelly_group_member,
            self.modeling_group.gaccess.members)
        # kelly makes request to join group
        membership_request = self.kelly_group_member.uaccess.create_group_membership_request(
            self.modeling_group)
        # let super user deny the request
        self.admin.uaccess.act_on_group_membership_request(
            membership_request, accept_request=False)
        # kelly should not be one of the members
        self.assertNotIn(
            self.kelly_group_member,
            self.modeling_group.gaccess.members)
