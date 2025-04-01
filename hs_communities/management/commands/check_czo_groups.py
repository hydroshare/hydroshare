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
from django_s3.exceptions import SessionException


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
    ["czo_shale-hills", "CZO Shale Hills", "SSHCZO"],
    ["czo_sierra", "CZO Southern Sierra", "SSCZO"],
    ["czo_christina", "CZO Christina", "CRBCZO"],
    ["czo_iml", "CZO IML", "IMLCZO"],
]


def set_quota_holder(resource, user):
    """ set quota holder and deal with failures """
    try:
        if resource.quota_holder != user:
            print("    SET QUOTA HOLDER FOR  {} {} TO {}"
                  .format(resource.short_id,
                          resource.title.encode('ascii', 'ignore'),
                          user.username))
            resource.set_quota_holder(user, user)
    except SessionException as ex:
        # some resources copied from www for testing do not exist in the backend,
        # hence need to skip these test artifects
        print(resource.short_id + ' raised SessionException when setting quota holder: '
              + ex.stderr)
        return False
    except AttributeError as ex:
        # when federation is not set up correctly, istorage does not have a session
        # attribute, hence raise AttributeError - ignore for testing
        print(resource.short_id + ' raised AttributeError when setting quota holder: '
              + str(ex))
        return False
    except ValueError as ex:
        # when federation is not set up correctly, istorage does not have a session
        # attribute, hence raise AttributeError - ignore for testing
        print(resource.short_id + ' raised ValueError when setting quota holder: '
              + str(ex))
        return False
    return True


def check_resource_prefix(user, group, resource, prefix, mapper, grantor):
    if not resource.title.startswith(prefix):
        print("    UNSHARING {} {}: prefix not {} (UNSHARING)"
              .format(resource.short_id,
                      resource.title.encode('ascii', 'ignore'),
                      prefix))
        # not in the user's resources
        UserResourcePrivilege.unshare(resource=resource,
                                      user=user,
                                      grantor=grantor)
        # not in the group's resources
        GroupResourcePrivilege.unshare(resource=resource,
                                       group=group,
                                       grantor=grantor)

        # Where does it really go?
        new_prefix = resource.title.split(" ")[0]
        if new_prefix in mapper:
            new_username = mapper[new_prefix][0]
            new_groupname = mapper[new_prefix][1]
            new_user = User.objects.get(username=new_username)
            new_group = Group.objects.get(name=new_groupname)
            print("    SHARING {} {} with user={} group={}"
                  .format(resource.short_id, resource.title.encode('ascii', 'ignore'),
                          new_username, new_groupname))
            UserResourcePrivilege.share(resource=resource,
                                        user=new_user,
                                        privilege=PrivilegeCodes.OWNER,
                                        grantor=grantor)
            GroupResourcePrivilege.share(resource=resource,
                                         group=new_group,
                                         privilege=PrivilegeCodes.VIEW,
                                         grantor=grantor)
        else:
            print("    ERROR {} {} unknown prefix {}"
                  .format(resource.short_id,
                          resource.title.encode('ascii', 'ignore'),
                          new_prefix))


def check_resource_owners(user1, user2, resource, grantor):
    """ check that each resource has the proper number of owners """

    owners = User.objects.filter(u2urp__resource=resource,
                                 u2urp__privilege=PrivilegeCodes.OWNER)
    if user1 not in owners:
        # fix it NOW
        print("    SHARING {} {} with first owner {}"
              .format(resource.short_id,
                      resource.title.encode('ascii', 'ignore'),
                      user1.username))
        UserResourcePrivilege.share(user=user1, resource=resource,
                                    privilege=PrivilegeCodes.OWNER, grantor=grantor)
        # first argument is also quota holder.
        set_quota_holder(resource, user1)

    # for CZO national group, there's only one owner.
    if user1 != user2 and user2 not in owners:

        # fix it NOW
        print("    SHARING {} {} with second owner {}"
              .format(resource.short_id,
                      resource.title.encode('ascii', 'ignore'),
                      user2.username))
        UserResourcePrivilege.share(user=user2, resource=resource,
                                    privilege=PrivilegeCodes.OWNER, grantor=grantor)

    for o in owners:
        if o.username != user1.username and o.username != user2.username:
            # fix it NOW
            print("    UNSHARING {} {} with owner {}"
                  .format(resource.short_id,
                          resource.title.encode('ascii', 'ignore'),
                          o.username))
            UserResourcePrivilege.unshare(user=o, resource=resource, grantor=grantor)


def check_resource_group(group, resource, grantor):
    """ check that a resource is in exactly one group """
    groups = Group.objects.filter(g2grp__resource=resource)
    if group not in groups:
        # fix it NOW
        print("    SHARING {} {} with group {}"
              .format(resource.short_id,
                      resource.title.encode('ascii', 'ignore'),
                      group.name))
        GroupResourcePrivilege.share(resource=resource,
                                     group=group,
                                     grantor=grantor,
                                     privilege=PrivilegeCodes.VIEW)

    for g in groups:
        if g != group:
            # fix it NOW
            print("    UNSHARING {} {} with group {}"
                  .format(resource.short_id,
                          resource.title.encode('ascii', 'ignore'),
                          g.name))
            GroupResourcePrivilege.unshare(resource=resource,
                                           group=group,
                                           grantor=grantor)


class Command(BaseCommand):
    help = "check czo setup for proper group and owners of each resource"

    def handle(self, *args, **options):
        national_user = User.objects.get(username='czo_national')
        czo_community = Community.objects.get(name='CZO National Community')

        czo_mapper = {}
        for czo in czo_setup:  # index by prefix
            czo_mapper[czo[2]] = czo

        # check each group in turn
        for czo in czo_setup:
            czo_username = czo[0]
            czo_groupname = czo[1]
            czo_prefix = czo[2]  # prefix for all titles for this group.

            print("CHECKING user {} against group {}".format(czo_username, czo_groupname))
            czo_user = User.objects.get(username=czo_username)
            czo_group = Group.objects.get(name=czo_groupname)

            user_resources = set(BaseResource.objects.filter(r2urp__user=czo_user))
            print("  There are {} user resources".format(len(user_resources)))
            # for r in user_resources:
            #     print("    {} {}".format(r.short_id, r.title.encode('ascii', 'ignore')))
            group_resources = set(BaseResource.objects.filter(r2grp__group=czo_group))
            print("  There are {} group resources".format(len(group_resources)))
            # for r in group_resources:
            #     print("    {} {}".format(r.short_id, r.title.encode('ascii', 'ignore')))

            # check that group is in the community
            if not Community.objects.filter(c2gcp__community=czo_community,
                                            c2gcp__group=czo_group).exists():
                print("    SHARING group {} with community {}"
                      .format(czo_group.name, czo_community.name))
                # fix it NOW
                GroupCommunityPrivilege.share(group=czo_group, community=czo_community,
                                              privilege=PrivilegeCodes.VIEW,
                                              grantor=national_user)

            # check whether all resources are owned by czo national
            for r in user_resources | group_resources:
                if not UserResourcePrivilege.objects.filter(user=national_user,
                                                            privilege=PrivilegeCodes.OWNER,
                                                            resource=r).exists():
                    print("    SHARING {} {} with czo national user"
                          .format(r.short_id, r.title.encode('ascii', 'ignore')))
                    UserResourcePrivilege.share(user=national_user,
                                                resource=r,
                                                privilege=PrivilegeCodes.OWNER,
                                                grantor=national_user)
                # set quota holder to CZO national
                set_quota_holder(r, national_user)

            # Now everything is owned by CZO national so we can remove other owners safely.

            if czo_user != national_user:
                # Check that all resources have the appropriate prefix
                for r in user_resources | group_resources:  # or r in user_resources for non-czo
                    check_resource_prefix(czo_user, czo_group, r, czo_prefix, czo_mapper, national_user)

                # refresh for user and group changes from above
                user_resources = set(BaseResource.objects.filter(r2urp__user=czo_user))
                group_resources = set(BaseResource.objects.filter(r2grp__group=czo_group))

                # Now every resource is filed in the appropriate group,
                # and non-matching resources are owned by CZO National.

                # group owner should own all group resources and vice versa.
                # This will only pick up changes for resources that had the proper prefix.

                if len(user_resources - group_resources) != 0:
                    print("  The following user resources are not group resources")
                    for r in (user_resources - group_resources):
                        check_resource_group(czo_group, r, national_user)

                    # refresh group membership
                    group_resources = set(BaseResource.objects.filter(r2grp__group=czo_group))

                if len(group_resources - user_resources) != 0:
                    print("  The following group resources are not user resources:")
                    for r in (group_resources - user_resources):
                        check_resource_owners(national_user, czo_user, r, national_user)

                    # refresh ownership
                    user_resources = set(BaseResource.objects.filter(r2urp__user=czo_user))

            else:
                # czo national user and group only runs this clause
                # no assumption that user resources and group resources are the same.
                # * user resources are all resources.
                # * group resources are those that come from multiple sources.

                # Check that all resources have the appropriate prefix
                for r in group_resources:  # no user_resources because that's everything
                    check_resource_prefix(czo_user, czo_group, r, czo_prefix,
                                          czo_mapper, national_user)
                # pick up changes from above
                group_resources = set(BaseResource.objects.filter(r2grp__group=czo_group))

                for r in group_resources:
                    check_resource_group(czo_group, r, national_user)

                # pick up changes from above
                group_resources = set(BaseResource.objects.filter(r2grp__group=czo_group))

                for r in group_resources:
                    check_resource_owners(national_user, czo_user, r, national_user)


def is_equal_to_as_set(l1, l2):
    """ return true if two lists contain the same content
    :param l1: first list
    :param l2: second list
    :return: whether lists match
    """
    # Note specifically that set(l1) == set(l2) does not work as expected.
    return len(set(l1).symmetric_difference(set(l2))) == 0
