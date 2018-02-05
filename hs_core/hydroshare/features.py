from django.contrib.auth.models import User, Group
from hs_access_control.models import PrivilegeCodes, \
    UserResourcePrivilege, UserGroupPrivilege, GroupResourcePrivilege
from hs_core.models import BaseResource
from django.db.models import Q
from pprint import pprint


class Features(object):
    """
    Features appropriate for machine learning analysis of our databases.
    """

    @staticmethod
    def resource_ownership():
        """ return (user, resource) tuples representing resource ownership """
        records = []
        for u in User.objects.all():
            owned = BaseResource.objects.filter(r2urp__user=u,
                                                r2urp__privilege=PrivilegeCodes.OWNER)
            for r in owned:
                records.append((u, r,))
        return records

    @staticmethod
    def group_ownership():
        """ return (user, group) tuples representing group ownership """
        records = []
        for u in User.objects.all():
            owned = Group.objects.filter(g2ugp__user=u,
                                         g2ugp__privilege=PrivilegeCodes.OWNER)
            for g in owned:
                records.append((u, g,))
        return records

    @staticmethod
    def resource_editors():
        """ return (user, resource) tuples representing resource editing privilege """
        records = []
        for u in User.objects.all():
            editable = BaseResource.objects.filter(r2urp__user=u,
                                                   r2urp__privilege__lte=PrivilegeCodes.CHANGE)
            for r in editable:
                records.append((u, r,))
        return records

    @staticmethod
    def group_editors():
        """ return (user, group) tuples representing group editing privilege """
        records = []
        for u in User.objects.all():
            editable = Group.objects.filter(g2ugp__user=u,
                                            g2ugp__privilege__lte=PrivilegeCodes.CHANGE)
            for g in editable:
                records.append((u, g,))
        return records
