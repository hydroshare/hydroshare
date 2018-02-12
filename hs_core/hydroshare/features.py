from django.contrib.auth.models import User, Group
from hs_access_control.models import PrivilegeCodes
from hs_core.models import BaseResource
from hs_core.search_indexes import BaseResourceIndex
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

    @staticmethod
    def resource_features(obj):
        ind = BaseResourceIndex()
        output = {}
        output['sample_medium'] = ind.prepare_sample_medium(obj)
        output['creator'] = ind.prepare_creator(obj)
        output['title'] = ind.prepare_title(obj)
        output['abstract'] = ind.prepare_abstract(obj)
        output['author_raw'] = ind.prepare_author_raw(obj)
        output['author'] = ind.prepare_author(obj)
        output['author_url'] = ind.prepare_author_url(obj)
        output['creator'] = ind.prepare_creator(obj)
        output['contributor'] = ind.prepare_contributor(obj)
        output['subject'] = ind.prepare_subject(obj)
        output['organization'] = ind.prepare_organization(obj)
        output['publisher'] = ind.prepare_publisher(obj)
        output['creator_email'] = ind.prepare_creator_email(obj)
        output['availability'] = ind.prepare_availability(obj)
        output['replaced'] = ind.prepare_replaced(obj)
        output['coverage'] = ind.prepare_coverage(obj)
        output['coverage_type'] = ind.prepare_coverage_type(obj)
        output['east'] = ind.prepare_east(obj)
        output['north'] = ind.prepare_north(obj)
        output['northlimit'] = ind.prepare_northlimit(obj)
        output['eastlimit'] = ind.prepare_eastlimit(obj)
        output['southlimit'] = ind.prepare_southlimit(obj)
        output['westlimit'] = ind.prepare_westlimit(obj)
        output['start_date'] = ind.prepare_start_date(obj)
        output['end_date'] = ind.prepare_end_date(obj)
        output['format'] = ind.prepare_format(obj)
        output['identifier'] = ind.prepare_identifier(obj)
        output['language'] = ind.prepare_language(obj)
        output['source'] = ind.prepare_source(obj)
        output['relation'] = ind.prepare_relation(obj)
        output['resource_type'] = ind.prepare_resource_type(obj)
        output['comment'] = ind.prepare_comment(obj)
        output['comments_count'] = ind.prepare_comments_count(obj)
        output['owner_login'] = ind.prepare_owner_login(obj)
        output['owner'] = ind.prepare_owner(obj)
        output['owners_count'] = ind.prepare_owners_count(obj)
        output['geometry_type'] = ind.prepare_geometry_type(obj)
        output['field_name'] = ind.prepare_field_name(obj)
        output['field_type'] = ind.prepare_field_type(obj)
        output['field_type_code'] = ind.prepare_field_type_code(obj)
        output['variable'] = ind.prepare_variable(obj)
        output['variable_type'] = ind.prepare_variable_type(obj)
        output['variable_shape'] = ind.prepare_variable_shape(obj)
        output['variable_descriptive_name'] = ind.prepare_variable_descriptive_name(obj)
        output['variable_speciation'] = ind.prepare_variable_speciation(obj)
        output['site'] = ind.prepare_site(obj)
        output['method'] = ind.prepare_method(obj)
        output['quality_level'] = ind.prepare_quality_level(obj)
        output['data_source'] = ind.prepare_data_source(obj)
        output['sample_medium'] = ind.prepare_sample_medium(obj)
        output['units'] = ind.prepare_units(obj)
        output['units_type'] = ind.prepare_units_type(obj)
        output['aggregation_statistics'] = ind.prepare_aggregation_statistics(obj)
        output['absolute_url'] = ind.prepare_absolute_url(obj)
        output['extra'] = ind.prepare_extra(obj)
        return output
