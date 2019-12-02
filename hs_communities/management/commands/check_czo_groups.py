"""
Check that CZO groups are set up properly.
If a resource is owned by a CZO owner, and not part of the CZO group,
  then add it to the group.
If a resource is not owned by CZO national, make it owned by CZO national.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from hs_access_control.models import UserResourcePrivilege, GroupResourcePrivilege, \
        GroupCommunityPrivilege, PrivilegeCodes, Community
from hs_core.models import BaseResource


czo_setup = [
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


class Command(BaseCommand):
    help = "check czo setup"

    def handle(self, *args, **options):
        national = User.objects.get(username='czo_national')
        prefixes = {}
        community = Community.objects.get(name='CZO National Community')

        for czo in czo_setup:  # index by prefix
            prefixes[czo[2]] = czo

        for czo in czo_setup:
            username = czo[0]
            groupname = czo[1]
            prefix = czo[2]  # prefix for all titles for this group.

            print("checking user {} against group {}".format(username, groupname))
            user = User.objects.get(username=username)
            group = Group.objects.get(name=groupname)

            # first check that group is in the community
            if not Community.objects.filter(c2gcp__community=community, c2gcp__group=group).exists():
                print("group {} is not in community {}".format(group.name, community.name))
                # fix it NOW
                GroupCommunityPrivilege.share(group=group, community=community,
                                              privilege=PrivilegeCodes.VIEW,
                                              grantor=national)

            user_resources = set(BaseResource.objects.filter(r2urp__user=user))
            group_resources = set(BaseResource.objects.filter(r2grp__group=group))
            print("  There are {} user resources".format(len(user_resources)))
            print("  There are {} group resources".format(len(group_resources)))

            if username != 'czo_national':
                # For every group but the master group, user should own all group resources
                if not is_equal_to_as_set(user_resources, group_resources):
                    if len(user_resources - group_resources) != 0:
                        print("  The following user resources are not group resources")
                        for r in (user_resources - group_resources):
                            print("   {} {}".format(r.short_id, r.title.encode('ascii', 'ignore')))
                            # Make it so NOW.
                            GroupResourcePrivilege.share(group=group,
                                                         resource=r,
                                                         privilege=PrivilegeCodes.VIEW,
                                                         grantor=user)
                    if len(group_resources - user_resources) != 0:
                        print("  The following group resources are not user resources")
                        for r in (group_resources - user_resources):
                            print("   {} {}".format(r.short_id, r.title.encode('ascii', 'ignore')))
                for r in group_resources:
                    if not r.title.startswith(prefix):
                        print("   Misfiled resource {} {}: prefix not {}".format(r.short_id,
                                                                                 r.title.encode(
                                                                                     'ascii',
                                                                                     'ignore'
                                                                                 ),
                                                                                 prefix))
                        # Fix it NOW
                        GroupResourcePrivilege.unshare(resource=r, group=group, grantor=national)
                    owners = User.objects.filter(u2urp__resource=r,
                                                 u2urp__privilege=PrivilegeCodes.OWNER)
                    if user not in owners:
                        print("  User {} does not own resource".format(username))
                        for o in owners:
                            print("    {}".format(o.username))
                    if national not in owners:
                        print("  CZO national user does not own resource {}".format(r.short_id))
                        UserResourcePrivilege.share(resource=r, user=national,
                                                    privilege=PrivilegeCodes.OWNER,
                                                    grantor=national)
                    owners = User.objects.filter(u2urp__resource=r,
                                                 u2urp__privilege=PrivilegeCodes.OWNER)
                    if owners.count() == 0:
                        print("  No owners for {} {}:".format(r.short_id,
                                                              r.title.encode('ascii', 'ignore')))
                        for o in owners:
                            print("    {}".format(o.username))
                    elif owners.count() == 1:
                        print("  Too few owners for {} {}:".format(r.short_id,
                                                                   r.title.encode('ascii',
                                                                                  'ignore')))
                        for o in owners:
                            print("    {}".format(o.username))

                    elif owners.count() == 2:
                        pass  # print("  Proper number of owners")

                    elif owners.count() > 2:
                        print("  Extra owners for {} {}:".format(r.short_id,
                                                                 r.title.encode('ascii', 'ignore')))
                        for o in owners:
                            print("    {}".format(o.username))

                    groups = Group.objects.filter(g2grp__resource=r)

                    if group not in groups:
                        print("   Resource not in group {}".format(groupname))

                    if groups.count() == 0:
                        print("  No groups for {} {}".format(r.short_id,
                                                             r.title.encode('ascii', 'ignore')))
                    elif groups.count() > 1:
                        print("  Extra groups for {} {}:".format(r.short_id,
                                                                 r.title.encode('ascii', 'ignore')))
                        for g in groups:
                            print("    {}".format(g.name))

            else:  # czo national user
                for r in group_resources:
                    print("checking {}".format(r.short_id))
                    if not r.title.startswith(prefix):
                        print("  Misfiled resource {} {}: prefix not {}".format(r.short_id,
                                                                                  r.title.encode(
                                                                                      'ascii',
                                                                                      'ignore'
                                                                                  ),
                                                                                  prefix))
                        # Fix it NOW
                        GroupResourcePrivilege.unshare(resource=r, group=group, grantor=national)

                    owners = User.objects.filter(u2urp__resource=r,
                                                 u2urp__privilege=PrivilegeCodes.OWNER)
                    if national not in owners:
                        print(" CZO national user does not own resource {}".format(r.short_id))

                    if owners.count() == 0:
                        print("  No owners for {} {}:".format(r.short_id,
                                                              r.title.encode('ascii',
                                                                             'ignore')))
                    if owners.count() == 2:
                        print("  Too many owners for {} {}:".format(r.short_id,
                                                                      r.title.encode('ascii',
                                                                                     'ignore')))
                        for o in owners:
                            print("    {}".format(o.username))

                    groups = Group.objects.filter(g2grp__resource=r)

                    if groups.count() == 0:
                        print("  No groups for {} {}:".format(r.short_id,
                                                              r.title.encode('ascii', 'ignore')))
                    elif groups.count() > 1:
                        print("  Extra groups for {} {}:".format(r.short_id,
                                                                 r.title.encode('ascii', 'ignore')))
                        for g in groups:
                            print("    {}".format(g.name))
                for r in user_resources - group_resources:
                    # print("resource {} is owned but not in czo_national group"
                    #       .format(r.short_id, r.title.encode('ascii', 'ignore')))
                    title = r.title
                    prefix = title.split(' ')[0]
                    # print("{} {} title prefix is {}".format(r.short_id,
                    #                                         r.title.encode('ascii', 'ignore'),
                    #                                         prefix))
                    if prefix in prefixes:
                        newgroupname = prefixes[prefix][1]

                        # print("  prefix {} is for group {}".format(prefix, newgroupname))
                        newgroup = Group.objects.get(name=newgroupname)
                        if newgroup not in Group.objects.filter(g2grp__resource=r):
                            print("  resource {} {} should be in group {}"
                                  .format(r.short_id,
                                          r.title.encode('ascii', 'ignore'),
                                          newgroupname))
                    else:
                        print("  prefix {} is unknown".format(prefix))


def is_equal_to_as_set(l1, l2):
    """ return true if two lists contain the same content
    :param l1: first list
    :param l2: second list
    :return: whether lists match
    """
    # Note specifically that set(l1) == set(l2) does not work as expected.
    return len(
        set(l1) & set(l2)) == len(
        set(l1)) and len(
            set(l1) | set(l2)) == len(
                set(l1))
