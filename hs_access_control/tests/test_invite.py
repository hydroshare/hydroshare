from django.test import TestCase
from django.contrib.auth.models import Group

from hs_access_control.models import PrivilegeCodes
from hs_access_control.models.invite import GroupCommunityRequest

from hs_access_control.tests.utilities import global_reset
from hs_core import hydroshare


class TestRequest(TestCase):

    def setUp(self):
        super(TestRequest, self).setUp()
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
        # self.cat.uaccess.share_group_with_user(self.cats, self.cat2, PrivilegeCodes.VIEW)

        # user 'cat' creates a new group called 'cats'
        self.cats = self.cat.uaccess.create_group(
            title='cats',
            description="This is the cats group",
            purpose="Our purpose to collaborate on begging.")

        # communities to use
        self.pets = self.dog.uaccess.create_community(
            'all kinds of pets',
            'collaboration on how to be a better pet.')

        self.pets.active = True
        self.pets.save()

    def test_community_invite_group_to_community(self):
        "share community with group according to invitation protocol"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.dog)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request created to connect group '{}' to community '{}'."\
            .format(self.cats.name, self.pets.name)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner is None)
        self.assertEqual(request.community_owner, self.dog)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.pending())
        self.assertTrue(request in GroupCommunityRequest.queued())
        self.assertTrue(request in GroupCommunityRequest.pending(responder=self.cat))
        self.assertTrue(request in GroupCommunityRequest.queued(requester=self.dog))
        self.assertFalse(self.cats in self.pets.member_groups)

        # colliding requests: approve instantly.
        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.cat)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request approved to connect group '{}' to community '{}'"\
                   " because there is a matching request."\
                   .format(self.cats.name, self.pets.name)
        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner, self.cat)
        self.assertEqual(request.community_owner, self.dog)
        self.assertTrue(request.redeemed)
        self.assertTrue(request.approved)
        self.assertFalse(request in GroupCommunityRequest.pending())
        self.assertFalse(request in GroupCommunityRequest.queued())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_group_request_group_join_community(self):
        "share community with group according to invitation protocol"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.cat)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request created to connect group '{}' to community '{}'."\
            .format(self.cats.name, self.pets.name)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.pending())
        self.assertTrue(request in GroupCommunityRequest.queued())
        self.assertTrue(request in GroupCommunityRequest.pending(responder=self.dog))
        self.assertTrue(request in GroupCommunityRequest.queued(requester=self.cat))

        self.assertFalse(self.cats in self.pets.member_groups)

        message, approved = GroupCommunityRequest.create_or_update(
            requester=self.dog, community=self.pets, group=self.cats)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request approved to connect group '{}' to community '{}'"\
                   " because there is a matching request."\
                   .format(self.cats.name, self.pets.name)
        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner, self.cat)
        self.assertEqual(request.community_owner, self.dog)
        self.assertTrue(request.redeemed)
        self.assertTrue(request.approved)
        self.assertFalse(request in GroupCommunityRequest.pending())
        self.assertFalse(request in GroupCommunityRequest.queued())
        self.assertFalse(request in GroupCommunityRequest.queued())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_community_invite_group_to_community_approve(self):
        "approve an invitation to join a community"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.dog)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request created to connect group '{}' to community '{}'."\
            .format(self.cats.name, self.pets.name)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner is None)
        self.assertEqual(request.community_owner, self.dog)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.pending())
        self.assertTrue(request in GroupCommunityRequest.queued())
        self.assertTrue(request in GroupCommunityRequest.pending(responder=self.cat))
        self.assertTrue(request in GroupCommunityRequest.queued(requester=self.dog))

        self.assertFalse(self.cats in self.pets.member_groups)

        message, success = request.accept_invitation(responder=self.cat)
        request = GroupCommunityRequest.objects.get(pk=request.pk)

        expected = "Request to connect group '{}' to community '{}' {}.".format(
            self.cats.name, self.pets.name, 'approved')
        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner is None)
        self.assertEqual(request.community_owner, self.dog)
        self.assertTrue(request.redeemed)
        self.assertTrue(request.approved)
        self.assertFalse(request in GroupCommunityRequest.pending())
        self.assertFalse(request in GroupCommunityRequest.queued())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_community_invite_group_to_community_decline(self):
        "reject an invitation to join a community"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.dog)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request created to connect group '{}' to community '{}'."\
            .format(self.cats.name, self.pets.name)
        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner is None)
        self.assertEqual(request.community_owner, self.dog)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.pending())
        self.assertTrue(request in GroupCommunityRequest.queued())
        self.assertTrue(request in GroupCommunityRequest.pending(responder=self.cat))
        self.assertTrue(request in GroupCommunityRequest.queued(requester=self.dog))

        self.assertFalse(self.cats in self.pets.member_groups)

        message, success = request.decline_invitation(responder=self.cat)
        request = GroupCommunityRequest.objects.get(pk=request.pk)

        expected = "Request to connect group '{}' to community '{}' {}.".format(
            self.cats.name, self.pets.name, 'declined')
        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner is None)
        self.assertEqual(request.community_owner, self.dog)
        self.assertTrue(request.redeemed)
        self.assertFalse(request.approved)
        self.assertFalse(request in GroupCommunityRequest.pending())
        self.assertFalse(request in GroupCommunityRequest.queued())

        self.assertFalse(self.cats in self.pets.member_groups)

    def test_group_request_group_join_community_approve(self):
        "reject a request to join a community"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.cat)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request created to connect group '{}' to community '{}'."\
            .format(self.cats.name, self.pets.name)
        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.pending())
        self.assertTrue(request in GroupCommunityRequest.queued())
        self.assertTrue(request in GroupCommunityRequest.pending(responder=self.dog))
        self.assertTrue(request in GroupCommunityRequest.queued(requester=self.cat))

        self.assertFalse(self.cats in self.pets.member_groups)

        message, success = request.approve_request(responder=self.dog)
        request = GroupCommunityRequest.objects.get(pk=request.pk)

        expected = "Request to connect group '{}' to community '{}' {}.".format(
            self.cats.name, self.pets.name, 'approved')
        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertTrue(request.redeemed)
        self.assertTrue(request.approved)
        self.assertFalse(request in GroupCommunityRequest.pending())
        self.assertFalse(request in GroupCommunityRequest.queued())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_group_request_group_join_community_decline(self):
        "reject a request to join a community"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.cat)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request created to connect group '{}' to community '{}'."\
            .format(self.cats.name, self.pets.name)
        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.pending())
        self.assertTrue(request in GroupCommunityRequest.queued())
        self.assertTrue(request in GroupCommunityRequest.pending(responder=self.dog))
        self.assertTrue(request in GroupCommunityRequest.queued(requester=self.cat))

        self.assertFalse(self.cats in self.pets.member_groups)

        message, success = request.decline_group_request(responder=self.dog)
        request = GroupCommunityRequest.objects.get(pk=request.pk)

        expected = "Request to connect group '{}' to community '{}' {}.".format(
            self.cats.name, self.pets.name, 'declined')
        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertTrue(request.redeemed)
        self.assertFalse(request.approved)
        self.assertFalse(request in GroupCommunityRequest.pending())
        self.assertFalse(request in GroupCommunityRequest.queued())

        self.assertFalse(self.cats in self.pets.member_groups)

    def test_community_invite_then_request(self):
        "request, then matching request"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.dog)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request created to connect group '{}' to community '{}'."\
            .format(self.cats.name, self.pets.name)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner is None)
        self.assertEqual(request.community_owner, self.dog)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.pending())
        self.assertTrue(request in GroupCommunityRequest.queued())
        self.assertTrue(request in GroupCommunityRequest.pending(responder=self.cat))
        self.assertTrue(request in GroupCommunityRequest.queued(requester=self.dog))

        self.assertFalse(self.cats in self.pets.member_groups)

        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.cat)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request approved to connect group '{}' to community '{}'"\
            " because there is a matching request."\
            .format(self.cats.name, self.pets.name)

        self.assertEqual(message, expected)

        # refresh objects to pick up async database changes
        request = GroupCommunityRequest.objects.get(pk=request.pk)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertEqual(request.community_owner, self.dog)
        self.assertTrue(request.redeemed)
        self.assertTrue(request.approved)
        self.assertFalse(request in GroupCommunityRequest.pending())
        self.assertFalse(request in GroupCommunityRequest.queued())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_group_request_then_invite(self):
        "request, then matching request"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.cat)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request created to connect group '{}' to community '{}'."\
            .format(self.cats.name, self.pets.name)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.pending())
        self.assertTrue(request in GroupCommunityRequest.queued())
        self.assertTrue(request in GroupCommunityRequest.pending(responder=self.dog))
        self.assertTrue(request in GroupCommunityRequest.queued(requester=self.cat))

        self.assertFalse(self.cats in self.pets.member_groups)

        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.dog)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request approved to connect group '{}' to community '{}'"\
            " because there is a matching request."\
            .format(self.cats.name, self.pets.name)

        self.assertEqual(message, expected)

        # refresh objects to pick up async database changes
        request = GroupCommunityRequest.objects.get(pk=request.pk)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertEqual(request.community_owner, self.dog)
        self.assertTrue(request.redeemed)
        self.assertTrue(request.approved)
        self.assertFalse(request in GroupCommunityRequest.pending())
        self.assertFalse(request in GroupCommunityRequest.queued())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_auto_approve(self):
        "request with auto-approvals"

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        self.pets.auto_approve_group = True
        self.pets.save()

        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.cat)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request auto-approved to connect group '{}' to community '{}'."\
            .format(self.cats.name, self.pets.name)

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
        self.assertFalse(request in GroupCommunityRequest.pending())
        self.assertFalse(request in GroupCommunityRequest.queued())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_group_request_owns_both(self):
        "request where requester owns both"

        self.assertTrue(self.dog.uaccess.can_share_community_with_user(
            self.pets, self.cat, PrivilegeCodes.OWNER))
        self.dog.uaccess.share_community_with_user(
            self.pets, self.cat, PrivilegeCodes.OWNER)

        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.cat)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request approved to connect group '{}' to community '{}'"\
            " because you own both."\
            .format(self.cats.name, self.pets.name)

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
        self.assertFalse(request in GroupCommunityRequest.pending())
        self.assertFalse(request in GroupCommunityRequest.queued())

        self.assertTrue(self.cats in self.pets.member_groups)

    def test_community_invite_update(self):
        "test repeated invites, requester from community"

        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.dog)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request created to connect group '{}' to community '{}'."\
            .format(self.cats.name, self.pets.name)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner is None)
        self.assertEqual(request.community_owner, self.dog)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.pending())
        self.assertTrue(request in GroupCommunityRequest.queued())
        self.assertTrue(request in GroupCommunityRequest.pending(responder=self.cat))
        self.assertTrue(request in GroupCommunityRequest.queued(requester=self.cat))
        self.assertFalse(self.cats in self.pets.member_groups)

        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.dog)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request updated: connect group '{}' to community '{}'."\
            .format(self.cats.name, self.pets.name)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertTrue(request.group_owner is None)
        self.assertEqual(request.community_owner, self.dog)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.pending())
        self.assertTrue(request in GroupCommunityRequest.queued())
        self.assertTrue(request in GroupCommunityRequest.pending(responder=self.cat))
        self.assertTrue(request in GroupCommunityRequest.queued(requester=self.dog))
        self.assertFalse(self.cats in self.pets.member_groups)

    def test_group_request_update(self):
        'test repeated requests, requester from group'
        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.cat)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request created to connect group '{}' to community '{}'."\
            .format(self.cats.name, self.pets.name)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.pending())
        self.assertTrue(request in GroupCommunityRequest.queued())
        self.assertTrue(request in GroupCommunityRequest.pending(responder=self.dog))
        self.assertTrue(request in GroupCommunityRequest.queued(requester=self.cat))

        self.assertFalse(self.cats in self.pets.member_groups)

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        message, approved = GroupCommunityRequest.create_or_update(
            group=self.cats, community=self.pets, requester=self.cat)
        request = GroupCommunityRequest.get_request(community=self.pets, group=self.cats)

        expected = "Request updated: connect group '{}' to community '{}'."\
            .format(self.cats.name, self.pets.name)

        self.assertEqual(message, expected)

        self.assertTrue(isinstance(request, GroupCommunityRequest))
        self.assertEqual(request.community, self.pets)
        self.assertEqual(request.group, self.cats)
        self.assertEqual(request.group_owner, self.cat)
        self.assertTrue(request.community_owner is None)
        self.assertFalse(request.redeemed)
        self.assertFalse(request.approved)
        self.assertTrue(request in GroupCommunityRequest.pending())
        self.assertTrue(request in GroupCommunityRequest.queued())
        self.assertTrue(request in GroupCommunityRequest.pending(responder=self.dog))
        self.assertTrue(request in GroupCommunityRequest.queued(requester=self.cat))

        self.assertFalse(self.cats in self.pets.member_groups)
