from django.test import TestCase
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from hs_access_control.models import PrivilegeCodes, GroupCommunityPrivilege,\
        GroupCommunityProvenance
from hs_access_control.models.invite import GroupCommunityInvite, GroupCommunityRequest

from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set
from hs_core import hydroshare
from pprint import pprint


class TestInvite(TestCase):

    def setUp(self):
        super(TestInvite, self).setUp()
        global_reset()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='administrator',
            last_name='couch',
            superuser=True,
            groups=[]
        )

        self.cat = hydroshare.create_account(
            'cat@gmail.com',
            username='cat',
            first_name='not a dog',
            last_name='last_name_cat',
            superuser=False,
            groups=[]
        )

        self.cat2 = hydroshare.create_account(
            'cat2@gmail.com',
            username='cat2',
            first_name='not a dog',
            last_name='last_name_cat2',
            superuser=False,
            groups=[]
        )

        self.dog = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            first_name='a little arfer',
            last_name='last_name_dog',
            superuser=False,
            groups=[]
        )

        self.dog2 = hydroshare.create_account(
            'dog2@gmail.com',
            username='dog2',
            first_name='a little arfer',
            last_name='last_name_dog2',
            superuser=False,
            groups=[]
        )

        # user 'dog' create a new group called 'dogs'
        self.dogs = self.dog.uaccess.create_group(
            title='dogs',
            description="This is the dogs group",
            purpose="Our purpose to collaborate on barking."
        )
        # self.dog.uaccess.share_group_with_user(self.dogs, self.dog2, PrivilegeCodes.VIEW)

        # user 'cat' creates a new group called 'cats'
        self.cats = self.cat.uaccess.create_group(
            title='cats',
            description="This is the cats group",
            purpose="Our purpose to collaborate on begging.")
        # self.cat.uaccess.share_group_with_user(self.cats, self.cat2, PrivilegeCodes.VIEW)

        # communities to use
        self.pets = self.dog.uaccess.create_community(
                'all kinds of pets',
                'collaboration on how to be a better pet.')

    def test_invite_group_to_community(self):
        "share community with group according to invitation protocol"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, invite, created = GroupCommunityInvite.create_or_update(
            group=self.cats, community=self.pets, community_owner=self.dog)

        expected = "Invitation created for group '{}' ({}) to join community '{}' ({})."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(invite, GroupCommunityInvite))
        self.assertEqual(invite.community, self.pets)
        self.assertEqual(invite.group, self.cats)
        self.assertTrue(invite.group_owner is None)
        self.assertEqual(invite.community_owner, self.dog)
        self.assertFalse(invite.redeemed)
        self.assertFalse(invite.approved)
        self.assertTrue(invite in GroupCommunityInvite.active_requests())
        self.assertFalse(self.cats in self.pets.member_groups)

        message, invite, success = invite.act(group_owner=self.cat, approved=True)
        expected = "Invitation from community '{}' to group '{}' {}.".format(
            self.pets.name, self.cats.name, 'approved')
        self.assertEqual(message, expected)

        self.assertTrue(isinstance(invite, GroupCommunityInvite))
        self.assertEqual(invite.community, self.pets)
        self.assertEqual(invite.group, self.cats)
        self.assertTrue(invite.group_owner, self.cat)
        self.assertEqual(invite.community_owner, self.dog)
        self.assertTrue(invite.redeemed)
        self.assertTrue(invite.approved)
        self.assertFalse(invite in GroupCommunityInvite.active_requests())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_request_group_join_community(self):
        "share community with group according to invitation protocol"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, request, created = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, group_owner=self.cat)

        expected = "Request created for group '{}' ({}) to join community '{}' ({})."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.active_requests())

        self.assertFalse(self.cats in self.pets.member_groups)

        message, invite, success = request.act(community_owner=self.dog, approved=True)
        expected = "Request from group '{}' to join community '{}' {}.".format(
            self.cats.name, self.pets.name, 'approved')
        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner, self.cat)
        self.assertEqual(request.community_owner, self.dog)
        self.assertTrue(request.redeemed)
        self.assertTrue(request.approved)
        self.assertFalse(request in GroupCommunityRequest.active_requests())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_invite_group_to_community_reject(self):
        "reject an invitation to join a community"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, invite, created = GroupCommunityInvite.create_or_update(
            group=self.cats, community=self.pets, community_owner=self.dog)

        expected = "Invitation created for group '{}' ({}) to join community '{}' ({})."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(invite, GroupCommunityInvite))
        self.assertEqual(invite.community, self.pets)
        self.assertEqual(invite.group, self.cats)
        self.assertTrue(invite.group_owner is None)
        self.assertEqual(invite.community_owner, self.dog)
        self.assertFalse(invite.redeemed)
        self.assertFalse(invite.approved)
        self.assertTrue(invite in GroupCommunityInvite.active_requests())

        self.assertFalse(self.cats in self.pets.member_groups)

        message, invite, success = invite.act(group_owner=self.cat, approved=False)
        expected = "Invitation from community '{}' to group '{}' {}.".format(
            self.pets.name, self.cats.name, 'declined')
        self.assertEqual(message, expected)

        self.assertTrue(isinstance(invite, GroupCommunityInvite))
        self.assertEqual(invite.community, self.pets)
        self.assertEqual(invite.group, self.cats)
        self.assertTrue(invite.group_owner, self.cat)
        self.assertEqual(invite.community_owner, self.dog)
        self.assertTrue(invite.redeemed)
        self.assertFalse(invite.approved)
        self.assertFalse(invite in GroupCommunityInvite.active_requests())

        self.assertFalse(self.cats in self.pets.member_groups)

    def test_request_group_join_community_reject(self):
        "reject a request to join a community"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, request, created = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, group_owner=self.cat)

        expected = "Request created for group '{}' ({}) to join community '{}' ({})."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.active_requests())

        self.assertFalse(self.cats in self.pets.member_groups)

        message, request, success = request.act(community_owner=self.dog, approved=True)
        expected = "Request from group '{}' to join community '{}' {}.".format(
            self.cats.name, self.pets.name, 'approved')
        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner, self.cat)
        self.assertEqual(request.community_owner, self.dog)
        self.assertTrue(request.redeemed)
        self.assertTrue(request.approved)
        self.assertFalse(request in GroupCommunityRequest.active_requests())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_invite_then_request(self):
        "invite, then matching request"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, invite, created = GroupCommunityInvite.create_or_update(
            group=self.cats, community=self.pets, community_owner=self.dog)

        expected = "Invitation created for group '{}' ({}) to join community '{}' ({})."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(invite, GroupCommunityInvite))
        self.assertEqual(invite.community, self.pets)
        self.assertEqual(invite.group, self.cats)
        self.assertTrue(invite.group_owner is None)
        self.assertEqual(invite.community_owner, self.dog)
        self.assertFalse(invite.redeemed)
        self.assertFalse(invite.approved)
        self.assertTrue(invite in GroupCommunityInvite.active_requests())

        self.assertFalse(self.cats in self.pets.member_groups)

        message, request, created = GroupCommunityRequest.create_or_update(
           group=self.cats, community=self.pets, group_owner=self.cat)

        expected = "Request approved for group '{}' ({}) to join community '{}' ({})"\
            " because there is a matching invitation."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id, self.dog.username)

        self.assertEqual(message, expected)

        # refresh objects to pick up async database changes
        invite = GroupCommunityInvite.objects.get(pk=invite.pk)
        request = GroupCommunityRequest.objects.get(pk=request.pk)

        self.assertTrue(isinstance(invite, GroupCommunityInvite))
        self.assertEqual(invite.community, self.pets)
        self.assertEqual(invite.group, self.cats)
        self.assertEqual(invite.group_owner, self.cat)
        self.assertEqual(invite.community_owner, self.dog)
        self.assertTrue(invite.redeemed)
        self.assertTrue(invite.approved)
        self.assertFalse(invite in GroupCommunityInvite.active_requests())

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertEqual(request.community_owner, self.dog)
        self.assertTrue(request.redeemed)
        self.assertTrue(request.approved)
        self.assertFalse(request in GroupCommunityRequest.active_requests())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_request_then_invite(self):
        "request, then matching invite"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, request, created = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, group_owner=self.cat)

        expected = "Request created for group '{}' ({}) to join community '{}' ({})."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.active_requests())

        self.assertFalse(self.cats in self.pets.member_groups)

        message, invite, created = GroupCommunityInvite.create_or_update(
            group=self.cats, community=self.pets, community_owner=self.dog)

        expected = "Invitation auto-approved for group '{}' ({}) to join community '{}' ({})"\
            " because there is a matching request."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id,
                    request.group_owner.username)

        self.assertEqual(message, expected)

        # refresh objects to pick up async database changes
        invite = GroupCommunityInvite.objects.get(pk=invite.pk)
        request = GroupCommunityRequest.objects.get(pk=request.pk)

        self.assertTrue(isinstance(invite, GroupCommunityInvite))
        self.assertEqual(invite.community, self.pets)
        self.assertEqual(invite.group, self.cats)
        self.assertEqual(invite.group_owner, self.cat)
        self.assertEqual(invite.community_owner, self.dog)
        self.assertTrue(invite.redeemed)
        self.assertTrue(invite.approved)
        self.assertFalse(invite in GroupCommunityInvite.active_requests())

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertEqual(request.community_owner, self.dog)
        self.assertTrue(request.redeemed)
        self.assertTrue(request.approved)
        self.assertFalse(request in GroupCommunityRequest.active_requests())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_auto_approve(self):
        "request with auto-approvals"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        self.pets.auto_approve = True
        self.pets.save()

        message, request, created = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, group_owner=self.cat)

        expected = "Request auto-approved for group '{}' ({}) to join community '{}' ({})."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id)

        self.assertEqual(message, expected)

        # refresh objects to pick up async database changes
        # request = GroupCommunityRequest.objects.get(pk=request.pk)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertEqual(request.community_owner, self.dog)
        self.assertTrue(request.redeemed)
        self.assertTrue(request.approved)
        self.assertFalse(request in GroupCommunityRequest.active_requests())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_invite_owns_both(self):
        "invite where owner owns both"

        self.assertTrue(self.dog.uaccess.can_share_community_with_user(
            self.pets, self.cat, PrivilegeCodes.OWNER))
        self.dog.uaccess.share_community_with_user(
            self.pets, self.cat, PrivilegeCodes.OWNER)

        message, invite, created = GroupCommunityInvite.create_or_update(
            group=self.cats, community=self.pets, community_owner=self.cat)

        expected = "Invitation auto-approved for group '{}' ({}) to join community '{}' ({})"\
            " because you also own the group."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id)

        self.assertEqual(message, expected)

        # refresh objects to pick up async database changes
        # invite = GroupCommunityRequest.objects.get(pk=request.pk)

        self.assertTrue(isinstance(invite, GroupCommunityInvite))
        self.assertEqual(invite.community, self.pets)
        self.assertEqual(invite.group, self.cats)
        self.assertEqual(invite.group_owner, self.cat)
        self.assertEqual(invite.community_owner, self.cat)
        self.assertTrue(invite.redeemed)
        self.assertTrue(invite.approved)
        self.assertFalse(invite in GroupCommunityInvite.active_requests())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_request_owns_both(self):
        "invite where owner owns both"

        self.assertTrue(self.dog.uaccess.can_share_community_with_user(
            self.pets, self.cat, PrivilegeCodes.OWNER))
        self.dog.uaccess.share_community_with_user(
            self.pets, self.cat, PrivilegeCodes.OWNER)

        message, request, created = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, group_owner=self.cat)

        expected = "Request auto-approved for group '{}' ({}) to join community '{}' ({})"\
            " because you also own the community."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id)

        self.assertEqual(message, expected)

        # refresh objects to pick up async database changes
        # request = GroupCommunityRequest.objects.get(pk=request.pk)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertEqual(request.community_owner, self.cat)
        self.assertTrue(request.redeemed)
        self.assertTrue(request.approved)
        self.assertFalse(request in GroupCommunityRequest.active_requests())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_invite_update(self):
        "test repeated invites"
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, invite, created = GroupCommunityInvite.create_or_update(
            group=self.cats, community=self.pets, community_owner=self.dog)

        expected = "Invitation created for group '{}' ({}) to join community '{}' ({})."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(invite, GroupCommunityInvite))
        self.assertEqual(invite.community, self.pets)
        self.assertEqual(invite.group, self.cats)
        self.assertTrue(invite.group_owner is None)
        self.assertEqual(invite.community_owner, self.dog)
        self.assertFalse(invite.redeemed)
        self.assertFalse(invite.approved)
        self.assertTrue(invite in GroupCommunityInvite.active_requests())
        self.assertFalse(self.cats in self.pets.member_groups)

        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, invite, created = GroupCommunityInvite.create_or_update(
            group=self.cats, community=self.pets, community_owner=self.dog)

        expected = "Invitation updated for group '{}' ({}) to join community '{}' ({})."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(invite, GroupCommunityInvite))
        self.assertEqual(invite.community, self.pets)
        self.assertEqual(invite.group, self.cats)
        self.assertTrue(invite.group_owner is None)
        self.assertEqual(invite.community_owner, self.dog)
        self.assertFalse(invite.redeemed)
        self.assertFalse(invite.approved)
        self.assertTrue(invite in GroupCommunityInvite.active_requests())
        self.assertFalse(self.cats in self.pets.member_groups)

    def test_request_update(self):
        'test repeated requests'
        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, request, created = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, group_owner=self.cat)

        expected = "Request created for group '{}' ({}) to join community '{}' ({})."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.active_requests())

        self.assertFalse(self.cats in self.pets.member_groups)

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, request, created = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, group_owner=self.cat)

        expected = "Request updated for group '{}' ({}) to join community '{}' ({})."\
            .format(self.cats.name, self.cats.id, self.pets.name, self.pets.id)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.active_requests())

        self.assertFalse(self.cats in self.pets.member_groups)

    def test_invite_act(self):
        'try to foul up the data and confuse the act procedure'

        message, invite, created = GroupCommunityInvite.create_or_update(
            group=self.cats, community=self.pets, community_owner=self.dog)
        invite.privilege = PrivilegeCodes.OWNER  # try for owner privleges :) 
        invite.save()
        message, invite, success = invite.act(group_owner=self.cat, approved=True)
        self.assertFalse(success)
        self.assertTrue(invite.redeemed)
        self.assertFalse(invite.approved)
        expected = "Invitation from community '{}' to group '{}': only view privilege is allowed."\
            .format(self.pets.name, self.cats.name)
        self.assertEqual(message, expected)

        message, invite, created = GroupCommunityInvite.create_or_update(
            group=self.cats, community=self.pets, community_owner=self.dog)
        invite.community_owner = self.cat  # foul up community ownership
        invite.save()
        message, invite, success = invite.act(group_owner=self.cat, approved=True)
        self.assertFalse(success)
        self.assertTrue(invite.redeemed)
        self.assertFalse(invite.approved)
        expected = "Invitation from community '{}' to group '{}': inviter no longer owns the community."\
            .format(self.pets.name, self.cats.name)
        self.assertEqual(message, expected)

        message, invite, created = GroupCommunityInvite.create_or_update(
            group=self.cats, community=self.pets, community_owner=self.dog)
        invite.act(group_owner=self.cat, approved=False)
        # Try to act on an invitation twice
        message, invite, success = invite.act(group_owner=self.cat, approved=True)
        self.assertFalse(success)
        self.assertTrue(invite.redeemed)
        self.assertFalse(invite.approved)
        expected = "Invitation from community '{}' to group '{}': already acted upon."\
            .format(self.pets.name, self.cats.name)
        self.assertEqual(message, expected)
        
        message, invite, created = GroupCommunityInvite.create_or_update(
            group=self.cats, community=self.pets, community_owner=self.dog)
        message, invite, success = invite.act(group_owner=self.dog, approved=True)  # foul up group owner
        self.assertFalse(success)
        self.assertTrue(invite.redeemed)
        self.assertFalse(invite.approved)
        expected = "Invitation from community '{}' to group '{}': you do not own the group."\
            .format(self.pets.name, self.cats.name)
        self.assertEqual(message, expected)

    def test_request_act(self):
        'try to foul up the data and confuse the act procedure'

        message, request, created = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, group_owner=self.cat)
        request.privilege = PrivilegeCodes.OWNER  # try for owner privleges :) 
        request.save()
        message, request, success = request.act(community_owner=self.dog, approved=True)
        self.assertFalse(success)
        self.assertTrue(request.redeemed)
        self.assertFalse(request.approved)
        expected = "Request from group '{}' to join community '{}': only view privilege is allowed."\
            .format(self.cats.name, self.pets.name)
        self.assertEqual(message, expected)

        message, request, created = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, group_owner=self.cat)
        request.group_owner = self.dog  # foul up group ownership
        request.save()
        message, request, success = request.act(community_owner=self.dog, approved=True)
        self.assertFalse(success)
        self.assertTrue(request.redeemed)
        self.assertFalse(request.approved)
        expected = "Request from group '{}' to join community '{}': requester no longer owns the group."\
            .format(self.cats.name, self.pets.name)
        self.assertEqual(message, expected)

        message, request, created = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, group_owner=self.cat)
        # Try to act on an invitation twice
        message, request, success = request.act(community_owner=self.dog, approved=False)
        self.assertTrue(success)
        self.assertTrue(request.redeemed)
        self.assertFalse(request.approved)
        message, request, success = request.act(community_owner=self.dog, approved=True)
        self.assertFalse(success)
        self.assertTrue(request.redeemed)
        self.assertFalse(request.approved)
        expected = "Request from group '{}' to join community '{}': already acted upon."\
            .format(self.cats.name, self.pets.name)
        self.assertEqual(message, expected)
        
        message, request, created = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, group_owner=self.cat)
        message, request, success = request.act(community_owner=self.cat, approved=True)  
        self.assertFalse(success)
        self.assertTrue(request.redeemed)
        self.assertFalse(request.approved)
        expected = "Request from group '{}' to join community '{}': you do not own the community."\
            .format(self.cats.name, self.pets.name)
        self.assertEqual(message, expected)
