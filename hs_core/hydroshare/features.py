from django.contrib.auth.models import User, Group
from hs_access_control.models import PrivilegeCodes
from hs_core.models import BaseResource
from hs_tracking.models import Variable
# from hs_core.hydroshare.utils import user_from_id
import re


class Features(object):
    """
    Features appropriate for machine learning analysis of our databases.
    """

    @staticmethod
    def resource_owners():
        """ return (user, resource) tuples representing resource owners """
        records = []
        for u in User.objects.all():
            owned = BaseResource.objects.filter(r2urp__user=u,
                                                r2urp__privilege=PrivilegeCodes.OWNER)
            for r in owned:
                records.append((u.username, r.short_id,))
        return records

    @staticmethod
    def group_owners():
        """ return (user, group) tuples representing group ownership """
        records = []
        for u in User.objects.all():
            owned = Group.objects.filter(g2ugp__user=u,
                                         g2ugp__privilege=PrivilegeCodes.OWNER)
            for g in owned:
                records.append((u.username, g.name,))
        return records

    @staticmethod
    def resource_editors():
        """ return (user, resource) tuples representing resource editing privilege """
        records = []
        for u in User.objects.all():
            editable = BaseResource.objects.filter(r2urp__user=u,
                                                   r2urp__privilege__lte=PrivilegeCodes.CHANGE)
            for r in editable:
                records.append((u.username, r.short_id,))
        return records

    @staticmethod
    def group_editors():
        """ return (user, group) tuples representing group editing privilege """
        records = []
        for u in User.objects.all():
            editable = Group.objects.filter(g2ugp__user=u,
                                            g2ugp__privilege__lte=PrivilegeCodes.CHANGE)
            for g in editable:
                records.append((u.username, g.name,))
        return records

    @staticmethod
    def resource_viewers(fromdate, todate):
        """ map of users who viewed each resource, according to date of access """
        expr = re.compile('/resource/([^/]+)/')  # home page of resource
        resource_visited_by_user = {}
        for v in Variable.objects.filter(name='visit',
                                         timestamp__gte=fromdate, timestamp__lte=todate):
            user = v.session.visitor.user
            if user is not None and \
               user.username != 'test' and user.username != 'demo':
                value = v.get_value()
                m = expr.search(value)  # home page of resource
                if m and m.group(1):
                    resource_id = m.group(1)
                    user_id = user.username
                    # print("user={} resource={} when={}".format(user_id, resource_id,
                    #     str(v.timestamp)))
                    if resource_id not in resource_visited_by_user:
                        resource_visited_by_user[resource_id] = set([user_id])
                    else:
                        resource_visited_by_user[resource_id].add(user_id)
        return resource_visited_by_user

    @staticmethod
    def visited_resources(fromdate, todate):
        """ map of users who viewed each resource, according to date of access """
        expr = re.compile('/resource/([^/]+)/')  # home page of resource
        user_visiting_resource = {}
        for v in Variable.objects.filter(name='visit',
                                         timestamp__gte=fromdate, timestamp__lte=todate):
            user = v.session.visitor.user
            if user is not None and \
               user.username != 'test' and user.username != 'demo':
                value = v.get_value()
                m = expr.search(value)  # home page of resource
                if m and m.group(1):
                    resource_id = m.group(1)
                    user_id = user.username
                    # print("user={} resource={} when={}".format(user_id, resource_id,
                    #     str(v.timestamp)))
                    if user_id not in user_visiting_resource:
                        user_visiting_resource[user_id] = set([resource_id])
                    else:
                        user_visiting_resource[user_id].add(resource_id)
        return user_visiting_resource

    @staticmethod
    def resource_downloads(fromdate, todate):
        expr = re.compile('\|resource_guid=([^|]+)\|')  # resource short id
        downloads = {}
        for v in Variable.objects.filter(timestamp__gte=fromdate, timestamp__lte=todate):
            user = v.session.visitor.user
            if user is not None and \
               user.username != 'test' and user.username != 'demo':
                user_id = user.username
                if v.name == 'download':
                    value = v.get_value()
                    # print("user:{} value:{} action:{}".format(user_id, value, v.name))
                    m = expr.search(value)  # resource short id
                    if m and m.group(1):
                        resource_id = m.group(1)
                        user_id = user.username
                        if resource_id not in downloads:
                            downloads[resource_id] = set([user_id])
                        else:
                            downloads[resource_id].add(user_id)
        return downloads

    @staticmethod
    def user_downloads(fromdate, todate):
        expr = re.compile('\|resource_guid=([^|]+)\|')  # resource short id
        downloads = {}
        for v in Variable.objects.filter(timestamp__gte=fromdate, timestamp__lte=todate):
            user = v.session.visitor.user
            if user is not None and \
               user.username != 'test' and user.username != 'demo':
                user_id = user.username
                if v.name == 'download':
                    value = v.get_value()
                    # print("user:{} value:{} action:{}".format(user_id, value, v.name))
                    m = expr.search(value)  # resource short id
                    if m and m.group(1):
                        resource_id = m.group(1)
                        user_id = user.username
                        if resource_id not in downloads:
                            downloads[user_id] = set([resource_id])
                        else:
                            downloads[user_id].add(resource_id)
        return downloads

    @staticmethod
    def resource_apps(fromdate, todate):
        expr = re.compile('\|resourceid=([^|]+)\|')  # resource short id
        apps = {}
        for v in Variable.objects.filter(timestamp__gte=fromdate, timestamp__lte=todate):
            user = v.session.visitor.user
            if user is not None and \
               user.username != 'test' and user.username != 'demo':
                user_id = user.username
                if v.name == 'app_launch':
                    value = v.get_value()
                    # print("user:{} value:{} action:{}".format(user_id, value, v.name))
                    m = expr.search(value)  # resource short id
                    if m and m.group(1):
                        resource_id = m.group(1)
                        user_id = user.username
                        if resource_id not in apps:
                            apps[resource_id] = set([user_id])
                        else:
                            apps[resource_id].add(user_id)
        return apps

    @staticmethod
    def user_apps(fromdate, todate):
        expr = re.compile('\|resourceid=([^|]+)\|')  # resource short id
        apps = {}
        for v in Variable.objects.filter(timestamp__gte=fromdate, timestamp__lte=todate):
            user = v.session.visitor.user
            if user is not None and \
               user.username != 'test' and user.username != 'demo':
                user_id = user.username
                if v.name == 'app_launch':
                    value = v.get_value()
                    # print("user:{} value:{} action:{}".format(user_id, value, v.name))
                    m = expr.search(value)  # resource short id
                    if m and m.group(1):
                        resource_id = m.group(1)
                        user_id = user.username
                        if resource_id not in apps:
                            apps[user_id] = set([resource_id])
                        else:
                            apps[user_id].add(resource_id)
        return apps
