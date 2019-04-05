"""
Utility functions for management commands for access control.
"""

from django.contrib.auth.models import User, Group
from hs_core.models import BaseResource
from hs_access_control.models.community import Community
import re


RE_INT = re.compile(r'^([1-9]\d*|0)$')


def group_from_name_or_id(gname):
    """ return a group object given either an id or a name """

    if RE_INT.match(gname):
        try:
            gid = int(gname)
            group = Group.objects.get(id=gid)
            return group
        except Group.DoesNotExist:
            print("group with id {} does not exist.".format(str(gid)))
            return None

    else:  # interpret as name
        groups = Group.objects.filter(name=gname)
        if groups.count() == 0:
            print("group '{}' not found.".format(gname))
            return None
        elif groups.count() == 1:
            group = groups[0]
            return group
        else:
            print("Group name {} is not unique. Please use group id instead:".format(gname))
            for g in groups:
                print("   '{}' (id={})".format(g.name, str(g.id)))
            return None


def community_from_name_or_id(cname):
    """ return a group object given either an id or a name """

    if RE_INT.match(cname):
        try:
            cid = int(cname)
            group = Community.objects.get(id=cid)
            return group
        except Community.DoesNotExist:
            print("community with id {} does not exist.".format(str(cid)))
            return None

    else:  # interpret as name
        communities = Community.objects.filter(name=cname)
        if communities.count() == 0:
            print("community with name '{}' does not exist.".format(cname))
            return None

        elif communities.count() == 1:
            community = communities[0]
            return community
        else:
            print("Community name '{}' is not unique. Please use community id instead:"
                  .format(cname))
            for g in communities:
                print("   '{}' (id={})".format(g.name, str(g.id)))
            return None


def user_from_name(uname):
    try:
        return User.objects.get(username=uname)
    except User.DoesNotExist:
        print("user with username '{}' does not exist.".format(uname))
        return None


def resource_from_id(id):
    try:
        return BaseResource.objects.get(short_id=id)
    except BaseResource.DoesNotExist:
        print("resource with id '{} does not exist.".format(id))
        return None
