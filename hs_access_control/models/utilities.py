from hs_access_control.models.privilege import UserResourcePrivilege, GroupResourcePrivilege, \
        UserGroupPrivilege, GroupCommunityPrivilege


def coarse_permissions(u, r):
    """ document the nature of permissions for resource r for user u """

    results = []
    # check raw user-resource privilege
    if UserResourcePrivilege.objects.filter(user=u, resource=r).exists():
        results.append("{} has user-resource privilege over '{}'"
                       .format(u.username, r.title))

    # check raw user-group privilege
    if UserGroupPrivilege.objects.filter(user=u, group__g2grp__resource=r).exists():
        results.append("{} has user-group-resource privilege over '{}'"
                       .format(u.username, r.title))

    # check whether members of peer group can view community
    # we want to exclude cases where the peer group is self.
    if UserGroupPrivilege.objects\
            .filter(user=u, group__g2gcp__community__c2gcp__group__g2grp__resource=r)\
            .exclude(pk__in=UserGroupPrivilege.objects.filter(user=u, group__g2grp__resource=r))\
            .exists():
        results.append("{} has user-group-community-group-resource privilege over '{}'"
                       .format(u.username, r.title))
    return results


def access_permissions(u, r):
    """ explain access for a specific user and resource """
    # verbs = ["undefined", "owns", "can edit", "can view", "cannot access"]
    results = list()

    # check raw user-resource privilege
    for q in UserResourcePrivilege.objects.filter(user=u, resource=r):
        # print("  * {} {} '{}'".format(u.username, verbs[q.privilege], r.title))
        results.append((q,))

    # check raw user-group-resource privilege
    for q in UserGroupPrivilege.objects.filter(user=u, group__g2grp__resource=r):
        for q2 in GroupResourcePrivilege.objects.filter(group=q.group, resource=r):
            results.append((q, q2,))

    # peer communities are given view privilege
    # This logic is complex. We want to prevent returns to the group from which we originated.
    # this will only happen if we start at a group with permission. So we prohibit that subcase
    # Check whether peers grant privilege by being in the same community
    for q in UserGroupPrivilege.objects\
            .filter(user=u,
                    group__gaccess__active=True,
                    group__g2gcp__community__c2gcp__allow_view=True,
                    group__g2gcp__community__c2gcp__group__gaccess__active=True,
                    group__g2gcp__community__c2gcp__group__g2grp__resource=r)\
            .exclude(pk__in=UserGroupPrivilege.objects.filter(user=u,
                                                              group__g2grp__resource=r)):
        for q2 in GroupCommunityPrivilege.objects.filter(
                group__gaccess__active=True,
                group=q.group,
                community__c2gcp__group__gaccess__active=True,
                community__c2gcp__group__g2grp__resource=r):
            for q3 in GroupCommunityPrivilege.objects.filter(
                    community=q2.community,
                    community__c2gcp__group__g2grp__resource=r):
                for q4 in GroupResourcePrivilege.objects\
                          .filter(group=q3.group, resource=r):
                    results.append((q, q2, q3, q4,))
    return results


def access_provenance(u, r):
    verbs = ["undefined", "owns", "can edit", "can view", "cannot access"]
    e = access_permissions(u, r)
    # pprint(e)
    output = "user {} {} resource '{}'\n"\
        .format(u.username, verbs[r.raccess.get_effective_privilege(u)], r.title)
    if r.raccess.immutable:
        output += "    '{}' is immutable: edit is replaced with view\n".format(r.title)
    for tuple in e:
        elements = list(tuple)
        found = False
        for e in elements:
            if isinstance(e, UserResourcePrivilege):
                output += "  * user {} {} resource.\n".format(e.user.username, verbs[e.privilege])
            elif isinstance(e, UserGroupPrivilege):
                output += "  * user {} {} group {},\n".format(e.user.username,
                                                              verbs[e.privilege],
                                                              e.group.name)
            elif isinstance(e, GroupResourcePrivilege):
                output += "    which {} resource.\n".format(verbs[e.privilege])
            elif isinstance(e, GroupCommunityPrivilege):
                if not found:
                    output += "    which {} community {},\n"\
                              .format(verbs[e.privilege], e.community.name)
                    found = True
                else:
                    output += "    which {} resources of group {},\n"\
                              .format(verbs[e.privilege], e.group.name)

    return output
