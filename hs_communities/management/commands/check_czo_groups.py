"""
Check that CZO groups are set up properly.
If a resource is owned by a CZO owner, and not part of the CZO group,
  then add it to the group.
If a resource is in a CZO group and not owned by the corresponding group owner,
  then make it owned by that owner.
If a resource owned by a CZO group owner is not owned by CZO national,
  then make it owned by CZO national.
If a resource has an inappropriate prefix for a group,
  then unshare it with that group and share with the appropriate group.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from hs_access_control.models import UserResourcePrivilege, GroupResourcePrivilege, \
        GroupCommunityPrivilege, PrivilegeCodes, Community
from hs_core.models import BaseResource
from django_irods.icommands import SessionException


# Details of CZO setup.
# This should be updated as groups are added.
czo_setup = [
    # group owner    group name      title prefix
    ["czo_national", "CZO National", "Cross-CZO"],
    ["czo_boulder", "CZO Boulder", "BCCZO"],
    ["czo_calhoun", "CZO Calhoun", "CCZO"],
    ["czo_catalina-jemez", "CZO Catalina-Jemez", "CJCZO"],
    ["czo_eel", "CZO Eel", "ERCZO"],
    ["czo_luquillo", "CZO Luquillo", "LCZO"],
    ["czo_reynolds", "CZO Reynolds", "RCCZO"],
    ["czo_shale-hills", "CZO Shale-Hills", "SSHCZO"],
    ["czo_sierra", "CZO Sierra", "SSCZO"],
    ["czo_christina", "CZO Christina", "CRBCZO"],
]


def set_quota_holder(resource, user):
    """ set quota holder and deal with iRODS failures """
    try:
        if resource.get_quota_holder() != user:
            resource.set_quota_holder(user, user)
    except SessionException as ex:
        # some resources copied from www for testing do not exist in the iRODS backend,
        # hence need to skip these test artifects
        print(resource.short_id + ' raised SessionException when setting quota holder: ' +
              ex.stderr)
        return False
    except AttributeError as ex:
        # when federation is not set up correctly, istorage does not have a session
        # attribute, hence raise AttributeError - ignore for testing
        print(resource.short_id + ' raised AttributeError when setting quota holder: ' +
              ex.message)
        return False
    except ValueError as ex:
        # when federation is not set up correctly, istorage does not have a session
        # attribute, hence raise AttributeError - ignore for testing
        print(resource.short_id + ' raised ValueError when setting quota holder: ' +
              ex.message)
        return False
    return True


def check_resource_owners(user1, user2, resource, grantor):
    """ check that each resource has the proper number of owners """

    owners = User.objects.filter(u2urp__resource=resource,
                                 u2urp__privilege=PrivilegeCodes.OWNER)
    if user1 not in owners:
        print("resource {} {} add owner {}".format(resource.short_id,
                                                   resource.title.encode('ascii',
                                                                         'ignore'),
                                                   user1.username))
        # fix it NOW
        UserResourcePrivilege.share(user=user1, resource=resource,
                                    privilege=PrivilegeCodes.OWNER, grantor=grantor)
        set_quota_holder(resource, user1)

    # for CZO national group, there's only one owner.
    if user1 != user2 and user2 not in owners:
        print("resource {} {} add owner {}".format(resource.short_id,
                                                   resource.title.encode('ascii',
                                                                         'ignore'),
                                                   user2.username))
        # fix it NOW
        UserResourcePrivilege.share(user=user2, resource=resource,
                                    privilege=PrivilegeCodes.OWNER, grantor=grantor)

    for o in owners:
        if o != user1 and o != user2:
            print("resource {} {} inappropriate owner {}".format(resource.short_id,
                                                                 resource.title.encode('ascii',
                                                                                       'ignore'),
                                                                 o.username))
            # fix it NOW
            UserResourcePrivilege.unshare(user=o, resource=resource, grantor=grantor)


def check_resource_group(group, resource, grantor):
    """ check that a resource is in exactly one group """
    groups = Group.objects.filter(g2grp__resource=resource)

    if group not in groups:
        print("   Resource {} {} not in group {} SHARED"
              .format(resource.short_id,
                      resource.title.encode('ascii', 'ignore'),
                      group.name))
        # fix it NOW
        GroupResourcePrivilege.share(resource=resource,
                                     group=group,
                                     grantor=grantor,
                                     privilege=PrivilegeCodes.VIEW)

    for g in groups:
        if g != group:
            print("{} {} extra group {} UNSHARED".format(resource.short_id,
                                                         resource.title.encode('ascii', 'ignore'),
                                                         g.name))
            # fix it NOW
            GroupResourcePrivilege.unshare(resource=resource,
                                           group=group,
                                           grantor=grantor)


class Command(BaseCommand):
    help = "check czo setup for proper group and owners of each resource"

    def handle(self, *args, **options):
        national_user = User.objects.get(username='czo_national')
        national_group = Group.objects.get(name='CZO National')
        czo_community = Community.objects.get(name='CZO National Community')

        prefixes = {}
        for czo in czo_setup:  # index by prefix
            prefixes[czo[2]] = czo

        # check each group in turn
        for czo in czo_setup:
            czo_username = czo[0]
            czo_groupname = czo[1]
            czo_prefix = czo[2]  # prefix for all titles for this group.

            print("checking user {} against group {}".format(czo_username, czo_groupname))
            czo_user = User.objects.get(username=czo_username)
            czo_group = Group.objects.get(name=czo_groupname)

            # first check that group is in the community
            if not Community.objects.filter(c2gcp__community=czo_community,
                                            c2gcp__group=czo_group).exists():
                print("group {} is not in community {} (SHARING)"
                      .format(czo_group.name, czo_community.name))
                # fix it NOW
                GroupCommunityPrivilege.share(group=czo_group, community=czo_community,
                                              privilege=PrivilegeCodes.VIEW,
                                              grantor=national_user)

            user_resources = set(BaseResource.objects.filter(r2urp__user=czo_user))
            print("  There are {} user resources".format(len(user_resources)))
            group_resources = set(BaseResource.objects.filter(r2grp__group=czo_group))
            print("  There are {} group resources".format(len(group_resources)))

            # check whether all resources are owned by czo national
            for r in user_resources | group_resources:
                if not UserResourcePrivilege.objects.filter(user=national_user,
                                                            privilege=PrivilegeCodes.OWNER,
                                                            resource=r).exists():
                    print("  {} {} not owned by czo national user"
                          .format(r.short_id, r.title.encode('ascii', 'ignore')))
                    UserResourcePrivilege.share(user=national_user,
                                                resource=r,
                                                privilege=PrivilegeCodes.OWNER,
                                                grantor=national_user)
                # set quota holder to CZO national
                set_quota_holder(r, national_user)

            # Now everything is owned by CZO national so we can remove other owners safely.

            # Check that all resources have the appropriate prefix
            for r in group_resources:  # or r in user_resources
                if not r.title.startswith(czo_prefix):
                    print("   Misfiled resource {} {}: prefix not {} (UNSHARING)"
                          .format(r.short_id, r.title.encode('ascii', 'ignore'), czo_prefix))
                    # Fix it NOW
                    # not in the user's resources
                    UserResourcePrivilege.unshare(resource=r,
                                                  user=czo_user,
                                                  grantor=national_user)
                    # not in the group's resources
                    GroupResourcePrivilege.unshare(resource=r,
                                                   group=czo_group,
                                                   grantor=national_user)
                    # Where does it really go?
                    new_prefix = r.title.split(" ")[0]
                    if new_prefix in prefixes:
                        new_username = prefixes[new_prefix][0]
                        new_groupname = prefixes[new_prefix][1]
                        new_user = User.objects.get(username=new_username)
                        new_group = Group.objects.get(name=new_groupname)
                        print("{} {} SHARING with {} {}"
                              .format(r.short_id, r.title.encode('ascii', 'ignore'),
                                      new_username, new_groupname))
                        UserResourcePrivilege.share(resource=r,
                                                    user=new_user,
                                                    privilege=PrivilegeCodes.OWNER,
                                                    grantor=national_user)
                        GroupResourcePrivilege.share(resource=r,
                                                     group=new_group,
                                                     privilege=PrivilegeCodes.VIEW,
                                                     grantor=national_user)
                    else:
                        print("{} {} unknown prefix {}"
                              .format(r.short_id, r.title.encode('ascii', 'ignore'), new_prefix))

            # refresh for user and group changes from above
            user_resources = set(BaseResource.objects.filter(r2urp__user=czo_user))
            group_resources = set(BaseResource.objects.filter(r2grp__group=czo_group))

            if czo_user != national_user:
                # group owner should own all group resources and vice versa.
                if len(user_resources - group_resources) != 0:
                    print("  The following user resources are not group resources (SHARING)")
                    for r in (user_resources - group_resources):
                        print("   {} {}".format(r.short_id, r.title.encode('ascii', 'ignore')))
                        # Make it so NOW. Default to VIEW privilege (unused)
                        GroupResourcePrivilege.share(group=czo_group,
                                                     resource=r,
                                                     privilege=PrivilegeCodes.VIEW,
                                                     grantor=national_user)

                if len(group_resources - user_resources) != 0:
                    print("  The following group resources are not user resources (SHARING)")
                    for r in (group_resources - user_resources):
                        print("   {} {}".format(r.short_id, r.title.encode('ascii', 'ignore')))
                        # Make it so NOW.
                        UserResourcePrivilege.share(resource=r,
                                                    user=czo_user,
                                                    privilege=PrivilegeCodes.OWNER,
                                                    grantor=national_user)

                # pick up changes from above
                user_resources = set(BaseResource.objects.filter(r2urp__user=czo_user))
                group_resources = set(BaseResource.objects.filter(r2grp__group=czo_group))
                # at this point, user_resources and group_resources are the same.

                for r in user_resources:
                    check_resource_owners(national_user, czo_user, r, national_user)
                for r in group_resources:
                    check_resource_group(czo_group, r, national_user)

            else:  # czo national user and group

                for r in user_resources:
                    check_resource_owners(national_user, national_user, r, national_user)
                    check_resource_group(national_group, r, national_user)


def is_equal_to_as_set(l1, l2):
    """ return true if two lists contain the same content
    :param l1: first list
    :param l2: second list
    :return: whether lists match
    """
    # Note specifically that set(l1) == set(l2) does not work as expected.
    return len(set(l1).symmetric_difference(set(l2))) == 0
