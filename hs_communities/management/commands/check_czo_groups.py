"""
Check that CZO groups are set up properly.
If a resource is owned by a CZO owner, and not part of the CZO group, then add it to the group.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from hs_access_control.models import GroupResourcePrivilege, PrivilegeCodes
from hs_core.models import BaseResource


czo_setup = [
    ["czo_national", "CZO National"],
    ["czo_boulder", "CZO Boulder"],
    ["czo_calhoun", "CZO Calhoun"],
    ["czo_catalina-jemez", "CZO Catalina-Jemez"],
    ["czo_eel", "CZO Eel"],
    ["czo_luquillo", "CZO Luquillo"],
    ["czo_reynolds", "CZO Reynolds"],
    ["czo_shale-hills", "CZO Shale-Hills"],
    ["czo_sierra", "CZO Sierra"]
]


class Command(BaseCommand):
    help = "check czo setup"

    def handle(self, *args, **options):
        for czo in czo_setup:
            username = czo[0]
            groupname = czo[1]
            print("checking user {} against group {}".format(username, groupname))
            user = User.objects.get(username=username)
            group = Group.objects.get(name=groupname)
            user_resources = set(BaseResource.objects.filter(r2urp__user=user))
            group_resources = set(BaseResource.objects.filter(r2grp__group=group))
            print("  There are {} user resources".format(len(user_resources)))
            print("  There are {} group resources".format(len(group_resources)))

            if username != 'czo_national':
                if not is_equal_to_as_set(user_resources, group_resources):
                    if len(user_resources - group_resources) != 0:
                        print("  The following user resources are not group resources")
                        for r in (user_resources - group_resources):
                            print("    {} {}".format(r.short_id, r.title.encode('ascii', 'ignore')))
                            GroupResourcePrivilege.share(group=group,
                                                         resource=r,
                                                         privilege=PrivilegeCodes.VIEW,
                                                         grantor=user)
                    if len(group_resources - user_resources) != 0:
                        print("  The following group resources are not user resources")
                        for r in (group_resources - user_resources):
                            print("    {} {}".format(r.short_id, r.title.encode('ascii', 'ignore')))
                for r in user_resources | group_resources:
                    owners = User.objects.filter(u2urp__user=user, u2urp__resource=r,
                                                 u2urp__privilege=PrivilegeCodes.OWNER)
                    # print("  {} has {} owners".format(r.short_id, owners.count()))
                    if owners.count() == 0:
                        print("  No owners for {} {}:".format(r.short_id,
                                                              r.title.encode('ascii', 'ignore')))
                    elif owners.count() > 1:
                        print("  Extra owners for {} {}:".format(r.short_id,
                                                                 r.title.encode('ascii', 'ignore')))
                        for o in owners:
                            print("    {}".format(o.username))

                    groups = Group.objects.filter(g2grp__group=group, g2grp__resource=r)
                    # print("  {} has {} groups".format(r.short_id, groups.count()))
                    if groups.count() > 1:
                        print("  No groups for {} {}".format(r.short_id,
                                                             r.title.encode('ascii', 'ignore')))
                    elif groups.count() > 1:
                        print("  Extra groups for {} {}:".format(r.short_id,
                                                                 r.title.encode('ascii', 'ignore')))
                        for g in groups:
                            print("    {}".format(g.name))
            else:
                for r in group_resources:
                    owners = User.objects.filter(u2urp__user=user, u2urp__resource=r,
                                                 u2urp__privilege=PrivilegeCodes.OWNER)
                    # print("  {} has {} owners".format(r.short_id, owners.count()))
                    if owners.count() == 0:
                        print("  No owners for {} {}:".format(r.short_id,
                                                              r.title.encode('ascii', 'ignore')))
                    if owners.count() > 1:
                        print("  Extra owners for {} {}:".format(r.short_id,
                                                                 r.title.encode('ascii', 'ignore')))
                        for o in owners:
                            print("    {}".format(o.username))

                    groups = Group.objects.filter(g2grp__group=group, g2grp__resource=r)
                    # print("  {} has {} groups".format(r.short_id, groups.count()))
                    if groups.count() == 0:
                        print("  No groups for {} {}:".format(r.short_id,
                                                              r.title.encode('ascii', 'ignore')))
                    elif groups.count() > 1:
                        print("  Extra groups for {} {}:".format(r.short_id,
                                                                 r.title.encode('ascii', 'ignore')))
                        for g in groups:
                            print("    {}".format(g.name))


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
