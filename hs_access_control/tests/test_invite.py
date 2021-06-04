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
        invite, created = GroupCommunityInvite.create_or_update(
            group=self.cats, community=self.pets, community_owner=self.dog)

        self.assertTrue(created)

        self.assertTrue(isinstance(invite, GroupCommunityInvite))
        self.assertEqual(invite.community, self.pets)
        self.assertEqual(invite.group, self.cats)
        self.assertTrue(invite.group_owner is None)
        self.assertEqual(invite.community_owner, self.dog)
        self.assertFalse(invite.redeemed)
        self.assertFalse(invite.approved)
        self.assertTrue(invite in GroupCommunityInvite.active_requests()) 
        self.assertFalse(self.cats in self.pets.member_groups) 

        invite.act(group_owner=self.cat, approved=True)

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
        request, created = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, group_owner=self.cat)

        self.assertTrue(created)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.active_requests()) 

        self.assertFalse(self.cats in self.pets.member_groups) 

        request.act(community_owner=self.dog, approved=True)

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
        invite, created = GroupCommunityInvite.create_or_update(
            group=self.cats, community=self.pets, community_owner=self.dog)

        self.assertTrue(created)

        self.assertTrue(isinstance(invite, GroupCommunityInvite))
        self.assertEqual(invite.community, self.pets)
        self.assertEqual(invite.group, self.cats)
        self.assertTrue(invite.group_owner is None)
        self.assertEqual(invite.community_owner, self.dog)
        self.assertFalse(invite.redeemed)
        self.assertFalse(invite.approved)
        self.assertTrue(invite in GroupCommunityInvite.active_requests()) 

        self.assertFalse(self.cats in self.pets.member_groups) 

        invite.act(group_owner=self.cat, approved=False)

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
        request, created = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, group_owner=self.cat)

        self.assertTrue(created)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.active_requests()) 

        self.assertFalse(self.cats in self.pets.member_groups) 

        request.act(community_owner=self.dog, approved=True)

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
        invite, created = GroupCommunityInvite.create_or_update(
            group=self.cats, community=self.pets, community_owner=self.dog)

        self.assertTrue(created)

        self.assertTrue(isinstance(invite, GroupCommunityInvite))
        self.assertEqual(invite.community, self.pets)
        self.assertEqual(invite.group, self.cats)
        self.assertTrue(invite.group_owner is None)
        self.assertEqual(invite.community_owner, self.dog)
        self.assertFalse(invite.redeemed)
        self.assertFalse(invite.approved)
        self.assertTrue(invite in GroupCommunityInvite.active_requests()) 

        self.assertFalse(self.cats in self.pets.member_groups) 

        request, created = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, group_owner=self.cat)

        self.assertTrue(isinstance(invite, GroupCommunityInvite))
        self.assertEqual(invite.community, self.pets)
        self.assertEqual(invite.group, self.cats)
        self.assertTrue(invite.group_owner, self.cat)
        self.assertEqual(invite.community_owner, self.dog)
        self.assertTrue(invite.redeemed)
        self.assertTrue(invite.approved)
        self.assertFalse(invite in GroupCommunityInvite.active_requests()) 

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner, self.cat)
        self.assertEqual(request.community_owner, self.dog)
        self.assertTrue(request.redeemed)
        self.assertTrue(request.approved)
        self.assertFalse(request in GroupCommunityRequest.active_requests()) 

        self.assertTrue(self.cats in self.pets.member_groups) 
