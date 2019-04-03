from django.test import TestCase
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from hs_access_control.models import PrivilegeCodes, GroupCommunityPrivilege,\
        GroupCommunityProvenance, UserCommunityPrivilege, UserCommunityProvenance, \
        GroupResourcePrivilege
from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set, is_disjoint_from
from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin


class TestCommunities(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(TestCommunities, self).setUp()
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

        self.bat = hydroshare.create_account(
            'bat@gmail.com',
            username='bat',
            first_name='a little batty',
            last_name='last_name_bat',
            superuser=False,
            groups=[]
        )

        self.bat2 = hydroshare.create_account(
            'bat2@gmail.com',
            username='bat2',
            first_name='the ultimate bat',
            last_name='last_name_bat2',
            superuser=False,
            groups=[]
        )

        # user 'dog' create a new group called 'dogs'
        self.dogs = self.dog.uaccess.create_group(
            title='dogs',
            description="This is the dogs group",
            purpose="Our purpose to collaborate on barking."
        )
        self.dog.uaccess.share_group_with_user(self.dogs, self.dog2, PrivilegeCodes.VIEW)

        # user 'cat' creates a new group called 'cats'
        self.cats = self.cat.uaccess.create_group(
            title='cats',
            description="This is the cats group",
            purpose="Our purpose to collaborate on begging.")
        self.cat.uaccess.share_group_with_user(self.cats, self.cat2, PrivilegeCodes.VIEW)

        # user 'bat' creates a new group called 'bats'
        self.bats = self.bat.uaccess.create_group(
            title='bats',
            description="This is the bats group",
            purpose="Our purpose is to collaborate on guano.")
        self.bat.uaccess.share_group_with_user(self.bats, self.bat2, PrivilegeCodes.VIEW)

        # create a cross-over share that allows dog to share with cats.
        self.cat.uaccess.share_group_with_user(self.cats, self.dog, PrivilegeCodes.OWNER)
        # create a cross-over share that allows dog to share with bats.
        self.bat.uaccess.share_group_with_user(self.bats, self.dog, PrivilegeCodes.OWNER)

        self.holes = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.dog,
            title='all about dog holes',
            metadata=[],
        )
        self.dog.uaccess.share_resource_with_group(self.holes, self.dogs, PrivilegeCodes.VIEW)

        self.squirrels = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.dog,
            title='a list of squirrels to pester',
            metadata=[],
        )
        self.dog.uaccess.share_resource_with_group(self.squirrels, self.dogs, PrivilegeCodes.CHANGE)

        self.posts = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.cat,
            title='all about scratching posts',
            metadata=[],
        )
        self.cat.uaccess.share_resource_with_group(self.posts, self.cats, PrivilegeCodes.VIEW)

        self.claus = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.cat,
            title='bad jokes about claws',
            metadata=[],
        )
        self.cat.uaccess.share_resource_with_group(self.claus, self.cats, PrivilegeCodes.CHANGE)

        self.wings = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.bat,
            title='things with wings',
            metadata=[],
        )
        self.bat.uaccess.share_resource_with_group(self.wings, self.bats, PrivilegeCodes.VIEW)

        self.perches = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.bat,
            title='where to perch',
            metadata=[],
        )
        self.bat.uaccess.share_resource_with_group(self.perches, self.bats, PrivilegeCodes.CHANGE)

        # two communities to use
        self.pets = self.dog.uaccess.create_community(
                'all kinds of pets',
                'collaboration on how to be a better pet.')
        self.pests = self.bat.uaccess.create_community(
                'all kinds of pests',
                'collaboration on how to be a more effective pest.')

    def test_share_community_with_group(self):
        " share and unshare community with group "

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.VIEW))
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.CHANGE))
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.cats,
                                                                        PrivilegeCodes.VIEW))
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.cats,
                                                                        PrivilegeCodes.CHANGE))

        self.dog.uaccess.share_community_with_group(self.pets, self.dogs, PrivilegeCodes.VIEW)
        self.dog.uaccess.share_community_with_group(self.pets, self.cats, PrivilegeCodes.VIEW)

        # privilege object created
        ggp = UserCommunityPrivilege.objects.get(user=self.dog, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.OWNER)
        ggp = GroupCommunityPrivilege.objects.get(group=self.dogs, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)
        ggp = GroupCommunityPrivilege.objects.get(group=self.cats, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)

        # provenance object created
        ggp = UserCommunityProvenance.objects.get(user=self.dog, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.OWNER)
        ggp = GroupCommunityProvenance.objects.get(group=self.dogs, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)
        ggp = GroupCommunityProvenance.objects.get(group=self.cats, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)

        self.assertEqual(self.pets.get_effective_group_privilege(self.dogs),
                         PrivilegeCodes.VIEW)
        self.assertEqual(self.pets.get_effective_group_privilege(self.cats),
                         PrivilegeCodes.VIEW)

        self.assertTrue(self.holes in self.cat.uaccess.view_resources)
        self.assertTrue(self.holes not in self.cat.uaccess.edit_resources)

        self.assertTrue(self.cats in self.pets.member_groups)
        self.assertTrue(self.dogs in self.pets.member_groups)

        # group resources are unchanged.
        self.assertTrue(self.holes in self.dogs.gaccess.view_resources)
        self.assertFalse(self.holes in self.dogs.gaccess.edit_resources)
        self.assertTrue(self.posts in self.cats.gaccess.view_resources)
        self.assertFalse(self.posts in self.cats.gaccess.edit_resources)

        # group view resources do not reflect community privileges
        self.assertFalse(self.holes in self.cats.gaccess.view_resources)
        self.assertFalse(self.holes in self.cats.gaccess.edit_resources)
        self.assertFalse(self.posts in self.dogs.gaccess.view_resources)
        self.assertFalse(self.posts in self.dogs.gaccess.edit_resources)

        # reject ownership of community by a group
        self.assertFalse(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                         PrivilegeCodes.OWNER))
        with self.assertRaises(PermissionDenied):
            self.dog.uaccess.share_community_with_group(self.pets, self.dogs,
                                                        PrivilegeCodes.OWNER)

        # Privileges are unchanged by the previous act
        self.assertEqual(self.pets.get_effective_group_privilege(self.dogs),
                         PrivilegeCodes.VIEW)
        self.assertEqual(self.pets.get_effective_group_privilege(self.cats),
                         PrivilegeCodes.VIEW)

        # upgrade share privilege
        self.dog.uaccess.share_community_with_group(self.pets, self.dogs, PrivilegeCodes.CHANGE)

        # privilege object created
        ggp = GroupCommunityPrivilege.objects.get(group=self.dogs, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.CHANGE)

        # provenance object created
        ggp = GroupCommunityProvenance.objects.filter(group=self.dogs, community=self.pets)
        self.assertEqual(ggp.count(), 2)

        self.assertEqual(self.pets.get_effective_group_privilege(self.dogs), PrivilegeCodes.CHANGE)
        self.assertEqual(self.pets.get_effective_group_privilege(self.cats), PrivilegeCodes.VIEW)

        # user privileges reflect community privileges

        self.assertTrue(self.holes in self.dog.uaccess.view_resources)
        self.assertTrue(self.holes in self.dog.uaccess.edit_resources)
        self.assertTrue(self.holes in self.cat.uaccess.view_resources)
        self.assertTrue(self.holes not in self.cat.uaccess.edit_resources)

        # unshare community with group
        self.assertTrue(self.dog.uaccess.can_unshare_community_with_group(self.pets, self.dogs))
        self.dog.uaccess.unshare_community_with_group(self.pets, self.dogs)

        self.assertEqual(self.pets.get_effective_group_privilege(self.dogs), PrivilegeCodes.NONE)
        self.assertEqual(self.pets.get_effective_group_privilege(self.cats), PrivilegeCodes.VIEW)

        self.assertTrue(self.holes not in self.cat.uaccess.view_resources)
        self.assertTrue(self.holes not in self.cat.uaccess.edit_resources)

    def test_undo_share_community_with_group(self):
        " undo share of community with group "
        self.assertTrue(self.dog.uaccess.can_share_community_with_group(self.pets, self.dogs,
                                                                        PrivilegeCodes.CHANGE))
        self.dog.uaccess.share_community_with_group(self.pets, self.dogs, PrivilegeCodes.CHANGE)
        self.dog.uaccess.share_community_with_group(self.pets, self.cats, PrivilegeCodes.VIEW)

        self.assertEqual(self.pets.get_effective_group_privilege(self.dogs), PrivilegeCodes.CHANGE)
        self.assertEqual(self.pets.get_effective_group_privilege(self.cats), PrivilegeCodes.VIEW)

        self.assertTrue(self.dog.uaccess.can_undo_share_community_with_group(self.pets,
                                                                             self.dogs))

        self.dog.uaccess.undo_share_community_with_group(self.pets, self.dogs)

        self.assertEqual(self.pets.get_effective_group_privilege(self.dogs), PrivilegeCodes.NONE)
        self.assertEqual(self.pets.get_effective_group_privilege(self.cats), PrivilegeCodes.VIEW)

    def test_share_community_with_user(self):
        " share and unshare community with user "

        # first check permissions
        self.assertTrue(self.dog.uaccess.can_share_community_with_user(self.pets, self.dog2,
                                                                        PrivilegeCodes.VIEW))
        self.assertTrue(self.dog.uaccess.can_share_community_with_user(self.pets, self.dog2,
                                                                        PrivilegeCodes.CHANGE))
        self.assertTrue(self.dog.uaccess.can_share_community_with_user(self.pets, self.cat2,
                                                                        PrivilegeCodes.VIEW))
        self.assertTrue(self.dog.uaccess.can_share_community_with_user(self.pets, self.cat2,
                                                                        PrivilegeCodes.CHANGE))

        self.dog.uaccess.share_community_with_user(self.pets, self.dog2, PrivilegeCodes.VIEW)
        self.dog.uaccess.share_community_with_user(self.pets, self.cat2, PrivilegeCodes.VIEW)

        # privilege object created
        ggp = UserCommunityPrivilege.objects.get(user=self.dog, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.OWNER)
        ggp = UserCommunityPrivilege.objects.get(user=self.dog2, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)
        ggp = UserCommunityPrivilege.objects.get(user=self.cat2, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)

        # provenance object created
        ggp = UserCommunityProvenance.objects.get(user=self.dog, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.OWNER)
        ggp = UserCommunityProvenance.objects.get(user=self.dog2, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)
        ggp = UserCommunityProvenance.objects.get(user=self.cat2, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)

        self.assertEqual(self.pets.get_effective_user_privilege(self.dog2),
                         PrivilegeCodes.VIEW)
        self.assertEqual(self.pets.get_effective_user_privilege(self.cat2),
                         PrivilegeCodes.VIEW)

        self.assertTrue(self.cat2 in self.pets.member_users)
        self.assertTrue(self.dog2 in self.pets.member_users)

        # accept ownership of community by a user
        self.assertTrue(self.dog.uaccess.can_share_community_with_user(self.pets, self.dog2,
                                                                        PrivilegeCodes.OWNER))
        self.dog.uaccess.share_community_with_user(self.pets, self.dog2,
                                                   PrivilegeCodes.OWNER)
        # privilege object created
        ggp = UserCommunityPrivilege.objects.get(user=self.dog2, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.OWNER)

        # provenance object created
        ggp = UserCommunityProvenance.objects.filter(user=self.dog2, community=self.pets)
        self.assertEqual(ggp.count(), 2)

        # Privileges are changed by the previous act
        self.assertEqual(self.pets.get_effective_user_privilege(self.dog2),
                         PrivilegeCodes.OWNER)
        self.assertEqual(self.pets.get_effective_user_privilege(self.cat2),
                         PrivilegeCodes.VIEW)

        # downgrade share privilege
        self.dog.uaccess.share_community_with_user(self.pets, self.dog2, PrivilegeCodes.CHANGE)

        # privilege object created
        ggp = UserCommunityPrivilege.objects.get(user=self.dog2, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.CHANGE)

        # provenance object created
        ggp = UserCommunityProvenance.objects.filter(user=self.dog2, community=self.pets)
        self.assertEqual(ggp.count(), 3)

        self.assertEqual(self.pets.get_effective_user_privilege(self.dog2),
                         PrivilegeCodes.CHANGE)
        self.assertEqual(self.pets.get_effective_user_privilege(self.cat2),
                         PrivilegeCodes.VIEW)

        # unshare community with user
        self.assertTrue(self.dog.uaccess.can_unshare_community_with_user(self.pets, self.dog2))
        self.dog.uaccess.unshare_community_with_user(self.pets, self.dog2)

        self.assertEqual(self.pets.get_effective_user_privilege(self.dog2),
                         PrivilegeCodes.NONE)
        self.assertEqual(self.pets.get_effective_user_privilege(self.cat2),
                         PrivilegeCodes.VIEW)

    def test_undo_share_community_with_user(self):
        " undo share of community with group "
        self.assertTrue(self.dog.uaccess.can_share_community_with_user(self.pets, self.dog2,
                                                                        PrivilegeCodes.CHANGE))
        self.dog.uaccess.share_community_with_user(self.pets, self.dog2,
                                                    PrivilegeCodes.CHANGE)
        self.dog.uaccess.share_community_with_user(self.pets, self.cat2,
                                                    PrivilegeCodes.VIEW)

        self.assertEqual(self.pets.get_effective_user_privilege(self.dog2),
                         PrivilegeCodes.CHANGE)
        self.assertEqual(self.pets.get_effective_user_privilege(self.cat2),
                         PrivilegeCodes.VIEW)

        self.assertTrue(self.dog.uaccess.can_undo_share_community_with_user(self.pets,
                                                                             self.dog2))

        self.dog.uaccess.undo_share_community_with_user(self.pets, self.dog2)

        self.assertEqual(self.pets.get_effective_user_privilege(self.dog2),
                         PrivilegeCodes.NONE)
        self.assertEqual(self.pets.get_effective_user_privilege(self.cat2),
                         PrivilegeCodes.VIEW)

    def test_explanations(self):
        " explanations indicate why privileges are granted "
        self.dog.uaccess.share_community_with_group(self.pets, self.dogs, PrivilegeCodes.VIEW)
        self.dog.uaccess.share_community_with_group(self.pets, self.bats, PrivilegeCodes.VIEW)
        self.dog.uaccess.share_community_with_group(self.pets, self.cats, PrivilegeCodes.VIEW)

        self.assertTrue(self.dog2.uaccess.can_view_resource(self.holes))
        self.assertTrue(self.dog2.uaccess.can_view_resource(self.squirrels))
        self.assertTrue(self.dog2.uaccess.can_view_resource(self.posts))
        self.assertTrue(self.dog2.uaccess.can_view_resource(self.claus))
        self.assertTrue(self.dog2.uaccess.can_view_resource(self.wings))
        self.assertTrue(self.dog2.uaccess.can_view_resource(self.perches))

        self.assertTrue(self.cat2.uaccess.can_view_resource(self.holes))
        self.assertTrue(self.cat2.uaccess.can_view_resource(self.squirrels))
        self.assertTrue(self.cat2.uaccess.can_view_resource(self.posts))
        self.assertTrue(self.cat2.uaccess.can_view_resource(self.claus))
        self.assertTrue(self.cat2.uaccess.can_view_resource(self.wings))
        self.assertTrue(self.cat2.uaccess.can_view_resource(self.perches))

        self.assertTrue(self.bat2.uaccess.can_view_resource(self.holes))
        self.assertTrue(self.bat2.uaccess.can_view_resource(self.squirrels))
        self.assertTrue(self.bat2.uaccess.can_view_resource(self.posts))
        self.assertTrue(self.bat2.uaccess.can_view_resource(self.claus))
        self.assertTrue(self.bat2.uaccess.can_view_resource(self.wings))
        self.assertTrue(self.bat2.uaccess.can_view_resource(self.perches))

        self.assertFalse(self.dog2.uaccess.can_change_resource(self.holes))
        self.assertTrue(self.dog2.uaccess.can_change_resource(self.squirrels))
        self.assertFalse(self.dog2.uaccess.can_change_resource(self.posts))
        self.assertFalse(self.dog2.uaccess.can_change_resource(self.claus))
        self.assertFalse(self.dog2.uaccess.can_change_resource(self.wings))
        self.assertFalse(self.dog2.uaccess.can_change_resource(self.perches))

        self.assertFalse(self.cat2.uaccess.can_change_resource(self.holes))
        self.assertFalse(self.cat2.uaccess.can_change_resource(self.squirrels))
        self.assertFalse(self.cat2.uaccess.can_change_resource(self.posts))
        self.assertTrue(self.cat2.uaccess.can_change_resource(self.claus))
        self.assertFalse(self.cat2.uaccess.can_change_resource(self.wings))
        self.assertFalse(self.cat2.uaccess.can_change_resource(self.perches))

        self.assertFalse(self.bat2.uaccess.can_change_resource(self.holes))
        self.assertFalse(self.bat2.uaccess.can_change_resource(self.squirrels))
        self.assertFalse(self.bat2.uaccess.can_change_resource(self.posts))
        self.assertFalse(self.bat2.uaccess.can_change_resource(self.claus))
        self.assertFalse(self.bat2.uaccess.can_change_resource(self.wings))
        self.assertTrue(self.bat2.uaccess.can_change_resource(self.perches))

        self.assertTrue(is_equal_to_as_set(self.dog2.uaccess.view_groups,
                                           [self.dogs, self.cats, self.bats]))
        self.assertTrue(is_equal_to_as_set(self.cat2.uaccess.view_groups,
                                           [self.dogs, self.cats, self.bats]))
        self.assertTrue(is_equal_to_as_set(self.bat2.uaccess.view_groups,
                                           [self.dogs, self.cats, self.bats]))
        self.assertTrue(self.dog2.uaccess.can_view_group(self.dogs))
        self.assertTrue(self.dog2.uaccess.can_view_group(self.cats))
        self.assertTrue(self.dog2.uaccess.can_view_group(self.bats))

        self.assertTrue(self.cat2.uaccess.can_view_group(self.dogs))
        self.assertTrue(self.cat2.uaccess.can_view_group(self.cats))
        self.assertTrue(self.cat2.uaccess.can_view_group(self.bats))

        self.assertTrue(self.bat2.uaccess.can_view_group(self.dogs))
        self.assertTrue(self.bat2.uaccess.can_view_group(self.cats))
        self.assertTrue(self.bat2.uaccess.can_view_group(self.bats))

        self.assertTrue(is_equal_to_as_set(self.dog2.uaccess.edit_groups, []))
        self.assertTrue(is_equal_to_as_set(self.cat2.uaccess.edit_groups, []))
        self.assertTrue(is_equal_to_as_set(self.bat2.uaccess.edit_groups, []))

        self.assertFalse(self.dog2.uaccess.can_change_group(self.dogs))
        self.assertFalse(self.dog2.uaccess.can_change_group(self.cats))
        self.assertFalse(self.dog2.uaccess.can_change_group(self.bats))

        self.assertFalse(self.cat2.uaccess.can_change_group(self.dogs))
        self.assertFalse(self.cat2.uaccess.can_change_group(self.cats))
        self.assertFalse(self.bat2.uaccess.can_change_group(self.bats))

        self.assertFalse(self.bat2.uaccess.can_change_group(self.dogs))
        self.assertFalse(self.bat2.uaccess.can_change_group(self.cats))
        self.assertFalse(self.bat2.uaccess.can_change_group(self.bats))

        self.assertTrue(self.dogs.gaccess.viewers, [self.cat, self.cat2, self.dog,
                                                    self.dog2, self.bat, self.bat2])
        self.assertTrue(self.cats.gaccess.viewers, [self.cat, self.cat2, self.dog,
                                                    self.dog2, self.bat, self.bat2])
        self.assertTrue(self.bats.gaccess.viewers, [self.cat, self.cat2, self.dog,
                                                    self.dog2, self.bat, self.bat2])

        self.assertTrue(self.cat2.uaccess.view_resources,
                        [self.posts, self.holes, self.wings,
                         self.perches, self.claus, self.squirrels])
        self.assertTrue(self.dog2.uaccess.view_resources,
                        [self.posts, self.holes, self.wings,
                         self.perches, self.claus, self.squirrels])
        self.assertTrue(self.bat2.uaccess.view_resources,
                        [self.posts, self.holes, self.wings,
                         self.perches, self.claus, self.squirrels])

    def test_iteration(self):
        " iterate over resources in a community "

        # This tests the mechanism by which we will display a community view
        self.dog.uaccess.share_community_with_group(self.pets, self.dogs, PrivilegeCodes.VIEW)
        self.dog.uaccess.share_community_with_group(self.pets, self.bats, PrivilegeCodes.VIEW)
        self.dog.uaccess.share_community_with_group(self.pets, self.cats, PrivilegeCodes.VIEW)

        comms = self.dog.uaccess.communities
        self.assertTrue(is_equal_to_as_set(comms, [self.pets]))
        comm = comms[0]

        groupc = comm.get_groups_with_explicit_access(PrivilegeCodes.CHANGE)
        self.assertTrue(is_equal_to_as_set(groupc, []))

        groupv = comm.get_groups_with_explicit_access(PrivilegeCodes.VIEW)
        self.assertTrue(is_equal_to_as_set(groupv, [self.cats, self.bats, self.dogs]))

        for group in groupv:
            change_resources = comm.get_resources_with_explicit_access(self.dog, group,
                                                                       PrivilegeCodes.CHANGE)
            view_resources = comm.get_resources_with_explicit_access(self.dog, group,
                                                                     PrivilegeCodes.VIEW)
            self.assertTrue(is_disjoint_from(change_resources, view_resources))

            for r in change_resources:
                self.assertTrue(self.dog.uaccess.can_change_resource(r))
                self.assertTrue(self.dog.uaccess.can_view_resource(r))

            for r in view_resources:
                # if a resource can be changed by some other group, it can be changed.
                # if self has administrative privilege over a group, and that group
                # has CHANGE, it can be changed.
                if not self.dog.uaccess.owns_resource(r) and\
                   not GroupResourcePrivilege.objects.filter(
                        resource=r,
                        privilege=PrivilegeCodes.CHANGE,
                        group__g2ugp__user=self.dog).exists():
                    self.assertFalse(self.dog.uaccess.can_change_resource(r))
                self.assertTrue(self.dog.uaccess.can_view_resource(r))

    def test_privilege_elevation(self):
        """ test that privilege=CHANGE works properly """

        self.dog.uaccess.share_community_with_group(self.pets, self.dogs, PrivilegeCodes.VIEW)
        self.dog.uaccess.share_community_with_group(self.pets, self.cats, PrivilegeCodes.CHANGE)

        # privilege object created
        ggp = UserCommunityPrivilege.objects.get(user=self.dog, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.OWNER)
        ggp = GroupCommunityPrivilege.objects.get(group=self.dogs, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)
        ggp = GroupCommunityPrivilege.objects.get(group=self.cats, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.CHANGE)

        # provenance object created
        ggp = UserCommunityProvenance.objects.get(user=self.dog, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.OWNER)
        ggp = GroupCommunityProvenance.objects.get(group=self.dogs, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)
        ggp = GroupCommunityProvenance.objects.get(group=self.cats, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.CHANGE)

        self.assertEqual(self.pets.get_effective_group_privilege(self.dogs),
                         PrivilegeCodes.VIEW)
        self.assertEqual(self.pets.get_effective_group_privilege(self.cats),
                         PrivilegeCodes.CHANGE)

        # dogs has CHANGE over squirrels, and cats inherits CHANGE over squirrels
        self.assertTrue(self.squirrels in self.cat.uaccess.view_resources)
        self.assertTrue(self.squirrels in self.cat.uaccess.edit_resources)
        self.assertTrue(self.squirrels in self.cat2.uaccess.view_resources)
        self.assertTrue(self.squirrels in self.cat2.uaccess.edit_resources)

        # dogs has VIEW over holes, and cats inherits only VIEW over holes
        self.assertTrue(self.holes in self.cat.uaccess.view_resources)
        self.assertTrue(self.holes not in self.cat.uaccess.edit_resources)
        self.assertTrue(self.holes in self.cat2.uaccess.view_resources)
        self.assertTrue(self.holes not in self.cat2.uaccess.edit_resources)

        # group privileges do not reflect community privileges
        self.assertFalse(self.squirrels in self.cats.gaccess.view_resources)
        self.assertFalse(self.squirrels in self.cats.gaccess.edit_resources)
        self.assertFalse(self.holes in self.cats.gaccess.view_resources)
        self.assertFalse(self.holes in self.cats.gaccess.edit_resources)

    def test_privilege_squashing(self):
        """ setting allow_view to False disallows local group view """

        self.dog.uaccess.share_community_with_group(self.pets, self.dogs, PrivilegeCodes.VIEW)
        self.dog.uaccess.share_community_with_group(self.pets, self.cats, PrivilegeCodes.CHANGE)

        self.assertEqual(self.pets.get_effective_group_privilege(self.dogs),
                         PrivilegeCodes.VIEW)
        self.assertEqual(self.pets.get_effective_group_privilege(self.cats),
                         PrivilegeCodes.CHANGE)

        ggp = GroupCommunityPrivilege.objects.get(group=self.dogs, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.VIEW)
        ggp.allow_view = False
        ggp.save()
        ggp = GroupCommunityPrivilege.objects.get(group=self.cats, community=self.pets)
        self.assertEqual(ggp.privilege, PrivilegeCodes.CHANGE)
        ggp.allow_view = False
        ggp.save()

        self.assertEqual(self.pets.get_effective_group_privilege(self.dogs),
                         PrivilegeCodes.VIEW)
        self.assertEqual(self.pets.get_effective_group_privilege(self.cats),
                         PrivilegeCodes.CHANGE)

        # CHANGE privileges are not squashed by allow_view=False
        # (cat2 has only the privileges of the group cats)
        self.assertTrue(self.squirrels in self.cat2.uaccess.view_resources)
        self.assertTrue(self.squirrels in self.cat2.uaccess.edit_resources)
        self.assertTrue(self.holes in self.cat2.uaccess.view_resources)
        self.assertTrue(self.holes not in self.cat2.uaccess.edit_resources)

        self.assertTrue(self.cat2.uaccess.can_view_resource(self.squirrels))
        self.assertTrue(self.cat2.uaccess.can_change_resource(self.squirrels))
        self.assertTrue(self.cat2.uaccess.can_view_resource(self.holes))
        self.assertFalse(self.cat2.uaccess.can_change_resource(self.holes))

        # group privileges do not reflect community privileges
        self.assertFalse(self.squirrels in self.cats.gaccess.view_resources)
        self.assertFalse(self.squirrels in self.cats.gaccess.edit_resources)
        self.assertFalse(self.holes in self.cats.gaccess.view_resources)
        self.assertFalse(self.holes in self.cats.gaccess.edit_resources)

        # VIEW privileges are squashed by allow_view=False
        # (dog2 has only the privileges of the group dogs)
        self.assertTrue(self.posts not in self.dog2.uaccess.view_resources)
        self.assertTrue(self.posts not in self.dog2.uaccess.edit_resources)
        self.assertTrue(self.claus not in self.dog2.uaccess.view_resources)
        self.assertTrue(self.claus not in self.dog2.uaccess.edit_resources)

        self.assertFalse(self.dog2.uaccess.can_view_resource(self.posts))
        self.assertFalse(self.dog2.uaccess.can_change_resource(self.posts))
        self.assertFalse(self.dog2.uaccess.can_view_resource(self.claus))
        self.assertFalse(self.dog2.uaccess.can_change_resource(self.claus))

        # group privileges do not reflect community privileges
        self.assertFalse(self.posts in self.dogs.gaccess.view_resources)
        self.assertFalse(self.posts in self.dogs.gaccess.edit_resources)
        self.assertFalse(self.claus in self.dogs.gaccess.view_resources)
        self.assertFalse(self.claus in self.dogs.gaccess.edit_resources)
