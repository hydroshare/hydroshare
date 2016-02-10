"""
These functions enable matrix testing of access control. 
This is a method in which the whole state of the access 
control system is checked after every change. 
"""

__author__ = 'Alva'


import unittest
from django.http import Http404
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group
from pprint import pprint

from hs_access_control.models import UserAccess, GroupAccess, ResourceAccess, \
    UserResourcePrivilege, GroupResourcePrivilege, UserGroupPrivilege, PrivilegeCodes

from hs_core import hydroshare
from hs_core.models import GenericResource, BaseResource
from hs_core.testing import MockIRODSTestCaseMixin

def global_reset():
    UserResourcePrivilege.objects.all().delete()
    UserGroupPrivilege.objects.all().delete()
    GroupResourcePrivilege.objects.all().delete()
    UserAccess.objects.all().delete()
    GroupAccess.objects.all().delete()
    ResourceAccess.objects.all().delete()
    User.objects.all().delete()
    Group.objects.all().delete()
    BaseResource.objects.all().delete()

def is_equal_to_as_set(l1, l2):
    """ return true if two lists contain the same content
    :param l1: first list
    :param l2: second list
    :return: whether lists match
    """
    # Note specifically that set(l1) == set(l2) does not work as expected.
    return len(set(l1) & set(l2)) == len(set(l1)) and len(set(l1) | set(l2)) == len(set(l1))

def is_subset_of(l1, l2):
    """ return true if the first list is a subset of the second
    :param l1: first list
    :param l2: second list
    :return: whether first is a subset of second. 
    """
    return len(set(l1) | set(l2)) == len(set(l2))

def is_disjoint_from(l1, l2):
    """ return true if two lists contain completely different content. 
    :param l1: first list
    :param l2: second list
    :return: whether lists contain distinct content. 
    """
    return len(set(l1) & set(l2)) == 0

def assertResourceOwnersAre(self, this_resource, these_users):
    """ check all routines that depend upon ownership """
    self.assertTrue(is_equal_to_as_set(these_users, this_resource.raccess.owners))
    if not this_resource.raccess.immutable:
        self.assertTrue(is_subset_of(these_users, this_resource.raccess.edit_users))
    else:
        self.assertTrue(is_equal_to_as_set(this_resource.raccess.edit_users,[]))
    self.assertTrue(is_subset_of(these_users, this_resource.raccess.view_users))
    for u in these_users:
        self.assertTrue(u.uaccess.owns_resource(this_resource))
        if not this_resource.raccess.immutable:
            self.assertTrue(u.uaccess.can_change_resource(this_resource))
        else:
            self.assertFalse(u.uaccess.can_change_resource(this_resource))
        self.assertTrue(u.uaccess.can_change_resource_flags(this_resource))
        self.assertTrue(u.uaccess.can_view_resource(this_resource))
        self.assertTrue(u.uaccess.can_delete_resource(this_resource))
        self.assertTrue(this_resource in u.uaccess.owned_resources)
        if not this_resource.raccess.immutable:
            self.assertTrue(this_resource in u.uaccess.edit_resources)
        else:
            self.assertTrue(this_resource not in u.uaccess.edit_resources)
        self.assertTrue(this_resource in u.uaccess.view_resources)
        self.assertTrue(this_resource in u.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER))
        self.assertTrue(this_resource not in u.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE))
        self.assertTrue(this_resource not in u.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW))
        self.assertTrue(u in this_resource.raccess.view_users)
        if not this_resource.raccess.immutable: 
            self.assertTrue(u in this_resource.raccess.edit_users)
        else: 
            self.assertTrue(u not in this_resource.raccess.edit_users)
        self.assertTrue(u in this_resource.raccess.owners)
        self.assertEqual(this_resource.raccess.get_effective_privilege(u), PrivilegeCodes.OWNER)

def assertResourceEditorsAre(self, this_resource, these_users):
    """ these users are all editors without ownership """
    self.assertTrue(is_disjoint_from(these_users, this_resource.raccess.owners))
    if not this_resource.raccess.immutable:
        self.assertTrue(is_subset_of(these_users, this_resource.raccess.edit_users))
    else:
        self.assertTrue(is_equal_to_as_set(this_resource.raccess.edit_users, []))
    self.assertTrue(is_subset_of(these_users, this_resource.raccess.edit_users))
    for u in these_users:
        self.assertFalse(u.uaccess.owns_resource(this_resource))
        if not this_resource.raccess.immutable:
            self.assertTrue(u.uaccess.can_change_resource(this_resource))
        else:
            self.assertFalse(u.uaccess.can_change_resource(this_resource))
        self.assertFalse(u.uaccess.can_change_resource_flags(this_resource))
        self.assertTrue(u.uaccess.can_view_resource(this_resource))
        self.assertFalse(u.uaccess.can_delete_resource(this_resource))
        self.assertTrue(this_resource not in u.uaccess.owned_resources)
        self.assertTrue(this_resource in u.uaccess.edit_resources)
        self.assertTrue(is_equal_to_as_set(
            u.uaccess.owned_resources,
            u.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)))
        self.assertTrue(is_equal_to_as_set(
            set(u.uaccess.edit_resources)
            - set(u.uaccess.owned_resources),
            u.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)))
        self.assertTrue(this_resource in u.uaccess.view_resources)
        self.assertTrue(this_resource not in u.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER))
        self.assertTrue(this_resource in u.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE))
        self.assertTrue(this_resource not in u.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW))
        self.assertTrue(u in this_resource.raccess.view_users)
        self.assertTrue(u not in this_resource.raccess.owners)
        self.assertTrue(u in this_resource.raccess.edit_users)
        # if not this_resource.raccess.immutable:
        #     self.assertEqual(this_resource.raccess.get_combined_privilege(u), PrivilegeCodes.CHANGE)
        self.assertEqual(this_resource.raccess.get_effective_privilege(u), PrivilegeCodes.CHANGE)

def assertResourceViewersAre(self, this_resource, these_users):
    """ these users are all viewers without edit privilege or ownership"""
    self.assertTrue(is_disjoint_from(these_users, this_resource.raccess.owners))
    self.assertTrue(is_disjoint_from(these_users, this_resource.raccess.owners))
    self.assertTrue(is_disjoint_from(these_users, this_resource.raccess.edit_users))
    self.assertTrue(is_subset_of(these_users, this_resource.raccess.view_users))
    for u in these_users:
        self.assertFalse(u.uaccess.owns_resource(this_resource))
        self.assertFalse(u.uaccess.can_change_resource(this_resource))
        self.assertFalse(u.uaccess.can_change_resource_flags(this_resource))
        self.assertTrue(u.uaccess.can_view_resource(this_resource))
        self.assertFalse(u.uaccess.can_delete_resource(this_resource))
        self.assertTrue(this_resource not in u.uaccess.owned_resources)
        self.assertTrue(this_resource not in u.uaccess.edit_resources)
        self.assertTrue(this_resource in u.uaccess.view_resources)
        self.assertTrue(this_resource not in u.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER))
        self.assertTrue(this_resource not in u.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE))
        self.assertTrue(this_resource in u.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW))
        self.assertTrue(u in this_resource.raccess.view_users)
        self.assertTrue(u not in this_resource.raccess.owners)
        self.assertTrue(u not in this_resource.raccess.edit_users)
        # if not this_resource.raccess.immutable:
        #     self.assertEqual(this_resource.raccess.get_combined_privilege(u), PrivilegeCodes.VIEW)
        self.assertEqual(this_resource.raccess.get_effective_privilege(u), PrivilegeCodes.VIEW)

def assertResourceUserState(self, this_resource, owners, editors, viewers):
    self.assertTrue(is_disjoint_from(owners, editors))
    self.assertTrue(is_disjoint_from(owners, viewers))
    self.assertTrue(is_disjoint_from(editors, viewers))
    self.assertTrue(is_equal_to_as_set(this_resource.raccess.view_users, set(owners) | set(editors) | set(viewers)))
    assertResourceOwnersAre(self, this_resource, owners)
    assertResourceEditorsAre(self, this_resource, editors)
    assertResourceViewersAre(self, this_resource, viewers)

def assertOwnedResourcesAre(self, this_user, these_resources):
    """ this user owns these resources """
    self.assertTrue(is_equal_to_as_set(this_user.uaccess.owned_resources, these_resources))
    self.assertTrue(is_subset_of(these_resources, this_user.uaccess.view_resources))
    self.assertTrue(is_equal_to_as_set(these_resources, this_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)))
    self.assertTrue(is_disjoint_from(these_resources, this_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)))
    self.assertTrue(is_disjoint_from(these_resources, this_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)))
    for r in these_resources:
        self.assertTrue(this_user.uaccess.owns_resource(r))
        if not r.raccess.immutable:
            self.assertTrue(this_user.uaccess.can_change_resource(r))
        else:
            self.assertFalse(this_user.uaccess.can_change_resource(r))
        self.assertTrue(this_user.uaccess.can_change_resource_flags(r))
        self.assertTrue(this_user.uaccess.can_view_resource(r))
        self.assertTrue(this_user.uaccess.can_delete_resource(r))
        self.assertTrue(this_user in r.raccess.owners)
        if not r.raccess.immutable:
            self.assertTrue(this_user in r.raccess.edit_users)
            self.assertTrue(r in this_user.uaccess.edit_resources)
        else:
            self.assertTrue(this_user not in r.raccess.edit_users)
            self.assertTrue(r not in this_user.uaccess.edit_resources)
        self.assertTrue(this_user in r.raccess.view_users)
        # self.assertEqual(r.raccess.get_combined_privilege(this_user), PrivilegeCodes.OWNER)
        self.assertEqual(r.raccess.get_effective_privilege(this_user), PrivilegeCodes.OWNER)

def assertEditableResourcesAre(self, this_user, these_resources):
    """ this user owns these resources """
    self.assertTrue(is_disjoint_from(this_user.uaccess.owned_resources, these_resources))
    self.assertTrue(is_subset_of(these_resources, this_user.uaccess.view_resources))
    self.assertTrue(is_disjoint_from(these_resources, this_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)))
    self.assertTrue(is_equal_to_as_set(these_resources, this_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)))
    self.assertTrue(is_disjoint_from(these_resources, this_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)))
    for r in these_resources:
        self.assertFalse(this_user.uaccess.owns_resource(r))
        if not r.raccess.immutable:
            self.assertTrue(this_user.uaccess.can_change_resource(r))
        else:
            self.assertFalse(this_user.uaccess.can_change_resource(r))
        self.assertFalse(this_user.uaccess.can_change_resource_flags(r))
        self.assertTrue(this_user.uaccess.can_view_resource(r))
        self.assertFalse(this_user.uaccess.can_delete_resource(r))
        # these cannot be granted by groups
        self.assertFalse(this_user in r.raccess.owners)
        # these only apply to non-group privilege
        self.assertTrue(this_user in r.raccess.edit_users)
        self.assertTrue(this_user in r.raccess.view_users)
        self.assertTrue(r in this_user.uaccess.edit_resources)
        self.assertEqual(r.raccess.get_effective_privilege(this_user), PrivilegeCodes.CHANGE)

def assertViewableResourcesAre(self, this_user, these_resources):
    """ this user owns these resources """
    self.assertTrue(is_disjoint_from(these_resources, this_user.uaccess.owned_resources))
    self.assertTrue(is_disjoint_from(these_resources, this_user.uaccess.edit_resources))
    self.assertTrue(is_subset_of(these_resources, this_user.uaccess.view_resources))
    self.assertTrue(is_disjoint_from(these_resources, this_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)))
    self.assertTrue(is_disjoint_from(these_resources, this_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)))
    self.assertTrue(is_equal_to_as_set(these_resources, this_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)))
    for r in these_resources:
        self.assertFalse(this_user.uaccess.owns_resource(r))
        self.assertFalse(this_user.uaccess.can_change_resource(r))
        self.assertFalse(this_user.uaccess.can_change_resource_flags(r))
        self.assertTrue(this_user.uaccess.can_view_resource(r))
        self.assertFalse(this_user.uaccess.can_delete_resource(r))
        self.assertTrue(this_user not in r.raccess.owners)
        self.assertTrue(this_user not in r.raccess.edit_users)
        self.assertTrue(this_user in r.raccess.view_users)
        # if not r.raccess.immutable:
        #     self.assertEqual(r.raccess.get_combined_privilege(this_user), PrivilegeCodes.VIEW)
        self.assertEqual(r.raccess.get_effective_privilege(this_user), PrivilegeCodes.VIEW)

def assertUserResourceState(self, this_user, owned, editable, viewable):
    self.assertTrue(is_disjoint_from(owned, editable))
    self.assertTrue(is_disjoint_from(owned, viewable))
    self.assertTrue(is_disjoint_from(editable, viewable))
    assertOwnedResourcesAre(self, this_user, owned)
    assertEditableResourcesAre(self, this_user, editable)
    assertViewableResourcesAre(self, this_user, viewable)

def assertGroupOwnersAre(self, this_group, these_users):
    """ These users are owners of this group """
    self.assertTrue(is_equal_to_as_set(these_users, this_group.gaccess.owners))
    self.assertTrue(is_disjoint_from(these_users,
                                     set(this_group.gaccess.edit_users)
                                     - set(this_group.gaccess.owners)))
    self.assertTrue(is_disjoint_from(these_users,
                                     set(this_group.gaccess.members)
                                     - set(this_group.gaccess.owners)))
    for u in these_users:
        self.assertTrue(u.uaccess.owns_group(this_group))
        self.assertTrue(u.uaccess.can_change_group(this_group))
        self.assertTrue(u.uaccess.can_change_group_flags(this_group))
        self.assertTrue(u.uaccess.can_view_group(this_group))
        self.assertTrue(u.uaccess.can_delete_group(this_group))
        self.assertTrue(this_group in u.uaccess.owned_groups)
        self.assertTrue(this_group in u.uaccess.view_groups)
        self.assertTrue(this_group in u.uaccess.get_groups_with_explicit_access(PrivilegeCodes.OWNER))
        self.assertTrue(this_group not in u.uaccess.get_groups_with_explicit_access(PrivilegeCodes.CHANGE))
        self.assertTrue(this_group not in u.uaccess.get_groups_with_explicit_access(PrivilegeCodes.VIEW))
        self.assertEqual(this_group.gaccess.get_effective_privilege(u), PrivilegeCodes.OWNER)

def assertGroupEditorsAre(self, this_group, these_users):
    """ these_users are all editors without ownership """
    self.assertTrue(is_disjoint_from(these_users, this_group.gaccess.owners))
    self.assertTrue(is_equal_to_as_set(these_users,
                                       set(this_group.gaccess.edit_users)
                                       - set(this_group.gaccess.owners)))
    self.assertTrue(is_disjoint_from(these_users,
                                     set(this_group.gaccess.members)
                                     - set(this_group.gaccess.edit_users)))
    for u in these_users:
        self.assertFalse(u.uaccess.owns_group(this_group))
        self.assertTrue(u.uaccess.can_change_group(this_group))
        self.assertFalse(u.uaccess.can_change_group_flags(this_group))
        self.assertTrue(u.uaccess.can_view_group(this_group))
        self.assertFalse(u.uaccess.can_delete_group(this_group))
        self.assertTrue(this_group not in u.uaccess.owned_groups)
        self.assertTrue(this_group in u.uaccess.view_groups)
        self.assertTrue(this_group not in u.uaccess.get_groups_with_explicit_access(PrivilegeCodes.OWNER))
        self.assertTrue(this_group in u.uaccess.get_groups_with_explicit_access(PrivilegeCodes.CHANGE))
        self.assertTrue(this_group not in u.uaccess.get_groups_with_explicit_access(PrivilegeCodes.VIEW))
        self.assertEqual(this_group.gaccess.get_effective_privilege(u), PrivilegeCodes.CHANGE)

def assertGroupViewersAre(self, this_group, these_users):
    """ these_users are all viewers without ownership or edit """
    self.assertTrue(is_disjoint_from(these_users, this_group.gaccess.owners))
    self.assertTrue(is_disjoint_from(these_users,
                                     set(this_group.gaccess.edit_users)
                                     - set(this_group.gaccess.owners)))
    self.assertTrue(is_equal_to_as_set(these_users,
                                       set(this_group.gaccess.members)
                                       - set(this_group.gaccess.edit_users)))
    for u in these_users:
        self.assertFalse(u.uaccess.owns_group(this_group))
        self.assertFalse(u.uaccess.can_change_group(this_group))
        self.assertFalse(u.uaccess.can_change_group_flags(this_group))
        self.assertTrue(u.uaccess.can_view_group(this_group))
        self.assertFalse(u.uaccess.can_delete_group(this_group))
        self.assertTrue(this_group not in u.uaccess.owned_groups)
        self.assertTrue(this_group in u.uaccess.view_groups)
        self.assertTrue(this_group not in u.uaccess.get_groups_with_explicit_access(PrivilegeCodes.OWNER))
        self.assertTrue(this_group not in u.uaccess.get_groups_with_explicit_access(PrivilegeCodes.CHANGE))
        self.assertTrue(this_group in u.uaccess.get_groups_with_explicit_access(PrivilegeCodes.VIEW))
        self.assertEqual(this_group.gaccess.get_effective_privilege(u), PrivilegeCodes.VIEW)

def assertGroupUserState(self, this_group, owners, editors, viewers):
    self.assertTrue(is_disjoint_from(owners, editors))
    self.assertTrue(is_disjoint_from(owners, viewers))
    self.assertTrue(is_disjoint_from(editors, viewers))
    self.assertTrue(is_equal_to_as_set(this_group.gaccess.members, set(owners) | set(editors) | set(viewers)))
    self.assertTrue(is_equal_to_as_set(this_group.gaccess.edit_users, set(owners) | set(editors)))
    assertGroupOwnersAre(self, this_group, owners)
    assertGroupEditorsAre(self, this_group, editors)
    assertGroupViewersAre(self, this_group, viewers)

def assertOwnedGroupsAre(self, this_user, these_groups):
    """ This user is owner of these groups """
    self.assertTrue(is_equal_to_as_set(these_groups, this_user.uaccess.owned_groups))
    self.assertTrue(is_subset_of(these_groups, this_user.uaccess.edit_groups))
    self.assertTrue(is_subset_of(these_groups, this_user.uaccess.view_groups))
    self.assertTrue(is_disjoint_from(these_groups,
                                     set(this_user.uaccess.edit_groups)
                                     - set(this_user.uaccess.owned_groups)))
    self.assertTrue(is_disjoint_from(these_groups,
                                     set(this_user.uaccess.view_groups)
                                     - set(this_user.uaccess.owned_groups)))
    self.assertTrue(is_equal_to_as_set(these_groups, this_user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.OWNER)))
    self.assertTrue(is_disjoint_from(these_groups, this_user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.CHANGE)))
    self.assertTrue(is_disjoint_from(these_groups, this_user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.VIEW)))
    for g in these_groups:
        self.assertTrue(this_user in g.gaccess.owners)
        self.assertTrue(this_user in g.gaccess.edit_users)
        self.assertTrue(this_user in g.gaccess.members)
        self.assertTrue(this_user.uaccess.owns_group(g))
        self.assertTrue(this_user.uaccess.can_change_group(g))
        self.assertTrue(this_user.uaccess.can_change_group_flags(g))
        self.assertTrue(this_user.uaccess.can_view_group(g))
        self.assertTrue(this_user.uaccess.can_delete_group(g))
        self.assertEqual(g.gaccess.get_effective_privilege(this_user), PrivilegeCodes.OWNER)

def assertEditableGroupsAre(self, this_user, these_groups):
    """ This user is editor of these groups """
    self.assertTrue(is_disjoint_from(these_groups, this_user.uaccess.owned_groups))
    self.assertTrue(is_subset_of(these_groups, this_user.uaccess.edit_groups))
    self.assertTrue(is_subset_of(these_groups, this_user.uaccess.view_groups))
    self.assertTrue(is_equal_to_as_set(these_groups,
                                     set(this_user.uaccess.edit_groups)
                                     - set(this_user.uaccess.owned_groups)))
    self.assertTrue(is_disjoint_from(these_groups,
                                     set(this_user.uaccess.view_groups)
                                     - set(this_user.uaccess.owned_groups)
                                     - set(this_user.uaccess.edit_groups)))
    self.assertTrue(is_disjoint_from(these_groups, this_user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.OWNER)))
    self.assertTrue(is_equal_to_as_set(these_groups, this_user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.CHANGE)))
    self.assertTrue(is_disjoint_from(these_groups, this_user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.VIEW)))
    for g in these_groups:
        self.assertTrue(this_user not in g.gaccess.owners)
        self.assertTrue(this_user in g.gaccess.edit_users)
        self.assertTrue(this_user in g.gaccess.members)
        self.assertFalse(this_user.uaccess.owns_group(g))
        self.assertTrue(this_user.uaccess.can_change_group(g))
        self.assertFalse(this_user.uaccess.can_change_group_flags(g))
        self.assertTrue(this_user.uaccess.can_view_group(g))
        self.assertFalse(this_user.uaccess.can_delete_group(g))
        self.assertEqual(g.gaccess.get_effective_privilege(this_user), PrivilegeCodes.CHANGE)

def assertViewableGroupsAre(self, this_user, these_groups):
    """ This user can view these groups """
    self.assertTrue(is_disjoint_from(these_groups, this_user.uaccess.owned_groups))
    self.assertTrue(is_disjoint_from(these_groups, this_user.uaccess.edit_groups))
    self.assertTrue(is_subset_of(these_groups, this_user.uaccess.view_groups))
    self.assertTrue(is_equal_to_as_set(these_groups,
                                       set(this_user.uaccess.view_groups)
                                       - set(this_user.uaccess.edit_groups)
                                       - set(this_user.uaccess.owned_groups)))
    self.assertTrue(is_disjoint_from(these_groups,
                                     set(this_user.uaccess.edit_groups)
                                     - set(this_user.uaccess.view_groups)))
    self.assertTrue(is_disjoint_from(these_groups, this_user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.OWNER)))
    self.assertTrue(is_disjoint_from(these_groups, this_user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.CHANGE)))
    self.assertTrue(is_equal_to_as_set(these_groups, this_user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.VIEW)))
    for g in these_groups:
        self.assertTrue(this_user not in g.gaccess.owners)
        self.assertTrue(this_user not in g.gaccess.edit_users)
        self.assertTrue(this_user in g.gaccess.members)
        self.assertFalse(this_user.uaccess.owns_group(g))
        self.assertFalse(this_user.uaccess.can_change_group(g))
        self.assertFalse(this_user.uaccess.can_change_group_flags(g))
        self.assertTrue(this_user.uaccess.can_view_group(g))
        self.assertFalse(this_user.uaccess.can_delete_group(g))
        self.assertEqual(g.gaccess.get_effective_privilege(this_user), PrivilegeCodes.VIEW)

def assertUserGroupState(self, this_user, owned, editable, viewable):
    self.assertTrue(is_disjoint_from(owned, editable))
    self.assertTrue(is_disjoint_from(owned, viewable))
    self.assertTrue(is_disjoint_from(editable, viewable))
    self.assertTrue(is_equal_to_as_set(this_user.uaccess.view_groups, set(owned) | set(editable) | set(viewable)))
    assertOwnedGroupsAre(self, this_user, owned)
    assertEditableGroupsAre(self, this_user, editable)
    assertViewableGroupsAre(self, this_user, viewable)

def assertResourceGroupEditorsAre(self, this_resource, these_groups):
    """ these groups are all editors without ownership """
    self.assertTrue(is_equal_to_as_set(these_groups, this_resource.raccess.edit_groups))
    self.assertTrue(is_subset_of(these_groups, this_resource.raccess.view_groups))
    for g in these_groups:
        self.assertTrue(this_resource in g.gaccess.edit_resources)
        self.assertTrue(this_resource in g.gaccess.view_resources)
        self.assertTrue(this_resource not in g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER))
        self.assertTrue(this_resource in g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE))
        self.assertTrue(this_resource not in g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW))
        # self.assertEqual(this_resource.raccess.get_group_privilege(g), PrivilegeCodes.CHANGE)

def assertResourceGroupViewersAre(self, this_resource, these_groups):
    """ these groups are all editors without ownership """
    self.assertTrue(is_disjoint_from(these_groups, this_resource.raccess.edit_groups))
    self.assertTrue(is_subset_of(these_groups, this_resource.raccess.view_groups))
    self.assertTrue(is_equal_to_as_set(these_groups, set(this_resource.raccess.view_groups) - set(this_resource.raccess.edit_groups)))
    for g in these_groups:
        self.assertTrue(this_resource not in g.gaccess.edit_resources)
        self.assertTrue(this_resource in g.gaccess.view_resources)
        self.assertTrue(this_resource not in g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER))
        self.assertTrue(this_resource not in g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE))
        self.assertTrue(this_resource in g.gaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW))

def assertResourceGroupState(self, this_resource, editors, viewers):
    self.assertTrue(is_disjoint_from(editors, viewers))
    self.assertTrue(is_equal_to_as_set(this_resource.raccess.view_groups, set(editors) | set(viewers)))
    assertResourceGroupEditorsAre(self, this_resource, editors)
    assertResourceGroupViewersAre(self, this_resource, viewers)

def assertGroupEditableResourcesAre(self, this_group, these_resources):
    """ these resources are all editable by this_group"""
    self.assertTrue(is_subset_of(these_resources, this_group.gaccess.view_resources))
    self.assertTrue(is_equal_to_as_set(these_resources,this_group.gaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)))
    self.assertTrue(is_disjoint_from(these_resources,this_group.gaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)))
    self.assertTrue(is_equal_to_as_set(these_resources, this_group.gaccess.edit_resources))
    for r in these_resources:
        self.assertTrue(this_group in r.raccess.edit_groups)
        self.assertTrue(this_group in r.raccess.view_groups)

def assertGroupViewableResourcesAre(self, this_group, these_resources):
    """ these resources are all editable by this_group"""
    self.assertTrue(is_subset_of(these_resources, this_group.gaccess.view_resources))
    self.assertTrue(is_disjoint_from(these_resources,this_group.gaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)))
    self.assertTrue(is_equal_to_as_set(these_resources,this_group.gaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)))
    self.assertTrue(is_disjoint_from(these_resources, this_group.gaccess.edit_resources))
    for r in these_resources:
        self.assertTrue(this_group not in r.raccess.edit_groups)
        self.assertTrue(this_group in r.raccess.view_groups)

def assertGroupResourceState(self, this_group, editable, viewable):
    self.assertTrue(is_disjoint_from(editable, viewable))
    self.assertTrue(is_equal_to_as_set(this_group.gaccess.view_resources, set(editable) | set(viewable)))
    assertGroupEditableResourcesAre(self, this_group, editable)
    assertGroupViewableResourcesAre(self, this_group, viewable)

#######################
# printing functions to help with debugging
#######################

def getUserResourceState(this_user):
    return {"OWNER": this_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER),
            "CHANGE": this_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE),
            "VIEW": this_user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)}

def getUserGroupState(this_user):
    return {"OWNER": this_user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.OWNER),
            "CHANGE": this_user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.CHANGE),
            "VIEW": this_user.uaccess.get_groups_with_explicit_access(PrivilegeCodes.VIEW)}

def getGroupResourceState(this_group):
    return {"OWNER": this_group.gaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER),
            "CHANGE": this_group.gaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE),
            "VIEW": this_group.gaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)}

def printUserResourceState(this_user):
    pprint({'resources':{this_user: getUserResourceState(this_user)}})

def printUserGroupState(this_user):
    pprint({'groups':{this_user: getUserGroupState(this_user)}})

def printGroupResourceState(this_group):
    pprint({'resources':{this_group: getGroupResourceState(this_group)}})


