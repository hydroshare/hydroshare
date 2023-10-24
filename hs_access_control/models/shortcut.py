import json
import os
import tempfile
import copy

from django.db.models import Q
from django.http import JsonResponse
from hs_access_control.models.resource import ResourceAccess
from rest_framework import status
from rest_framework.decorators import api_view

from django.contrib.auth.models import User
from hs_access_control.models.privilege import PrivilegeBase
from hs_access_control.models.exceptions import PolymorphismError
from hs_core.models import BaseResource
import hs_access_control.signals
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

from hs_access_control.models.privilege import PrivilegeCodes, UserResourcePrivilege, \
    GroupResourcePrivilege

#############################################
# Shortcut query for data access
# These queries shortcut around the typical assumptions of access control by
# taking in keys rather than objects and shortcutting around the whole process
# of resolving keys to objects, as used in the rest of access control.
# This saves oodles of time in processing requests from REST calls.
#############################################


@api_view(['GET',])
def get_user_resource_privilege_endpoint(request, user_identifier, resource_id):
    privilege = get_user_resource_privilege(user_identifier, resource_id)
    return JsonResponse({"privilege": privilege}, status=status.HTTP_200_OK)


@api_view(['GET',])
def get_user_resources(request, user_identifier):
    privileges = get_user_resources_privileges(user_identifier)
    return JsonResponse(privileges, status=status.HTTP_200_OK)


def get_user_resources_privileges(email):

    user = User.objects.get(email=email)
    return user_resource_privileges(user)


def user_resource_privileges(user):
    owned_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
    editable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE, via_group=True)
    viewable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW, via_group=True)
    return {"owner": list(
        owned_resources.filter(resource_type="ExternalResource").values_list("short_id", flat=True).iterator()),
            "edit": list(editable_resources.filter(resource_type="ExternalResource").values_list("short_id",
                                                                                                 flat=True).iterator()),
            "view": list(viewable_resources.filter(resource_type="ExternalResource").values_list("short_id",
                                                                                                 flat=True).iterator())}


def get_user_resource_privilege(email, short_id):
    # return the privilege code 1-4 for a user and resource
    #
    # this never throws exceptions. It returns NONE:
    # - if a resource does not exist.
    # - if an email does not correspond to a user
    #
    # It returns the min of the privileges:
    # - if an email corresponds to more than one user account
    # - if a GUID somehow refers to more than one resource.
    from hs_access_control.models import ResourceAccess

    # public access
    privilege = list(ResourceAccess.objects.filter(
        resource__short_id=short_id).values_list('public', flat='True'))

    if (len(privilege) > 0) and privilege[0]:  # boolean
        privilege = [PrivilegeCodes.VIEW]
    else:
        privilege = [PrivilegeCodes.NONE]

    # user access
    privilege.extend(UserResourcePrivilege.objects.filter(
        user__email=email,
        resource__short_id=short_id).values_list('privilege', flat=True))

    # group access
    privilege.extend(GroupResourcePrivilege.objects.filter(
        Q(resource__short_id=short_id,
          group__gaccess__active=True,
          group__g2ugp__user__email=email)).values_list('privilege', flat=True))

    if len(privilege) > 0:
        return min(privilege)  # min of a list
    else:
        return PrivilegeCodes.NONE


#############################################
# Zone of effect queries for the resources affected
# by a change in user access, group access, etc.
#############################################
# 1. Adding a user to a group: affects that user only, all resources
#    that the group can see.
# 2. Adding a user to a resource access list: affects that user/resource pair only.
# 3. Adding or removing a resource from a group: affects that resource
#    and all users in that group.
# 4. Making a resource public or private: affects potentially all users.
#    in other words, there's no situation in which a change affects
# both multiple users and multiple resources.
# this sends signal access_changed.

def zone_of_influence(send=True, **kwargs):
    for k in kwargs:
        print("{}: {}".format(k, kwargs[k]))
    if len(kwargs) > 2:
        raise PolymorphismError("Too many arguments")
    if len(kwargs) < 2:
        raise PolymorphismError("Too few arguments")
    if 'resource' in kwargs:
        if 'user' in kwargs:
            users = [kwargs['user'].username]
            resources = [kwargs['resource'].short_id]
        elif 'group' in kwargs:
            users = list(User.objects
                             .filter(u2ugp__group=kwargs['group'])
                             .values_list('username', flat=True))
            resources = [kwargs['resource'].short_id]
    elif 'user' in kwargs and 'group' in kwargs:
        users = [kwargs['user'].username]
        resources = list(BaseResource.objects
                                     .filter(r2grp__group=kwargs['group'])
                                     .values_list('short_id', flat=True))
    if send:
        hs_access_control.signals.access_changed.send(
            sender=PrivilegeBase, users=users, resources=resources)
    else:
        return (users, resources)


def zone_of_publicity(send=True, **kwargs):
    for k in kwargs:
        print("{}: {}".format(k, kwargs[k]))
    if len(kwargs) > 1:
        raise PolymorphismError("Too many arguments")
    if len(kwargs) < 1:
        raise PolymorphismError("Too few arguments")
    if 'resource' in kwargs:
        users = []
        resources = [kwargs['resource'].short_id]
    else:
        raise PolymorphismError("Invalid argument")
    if send:
        hs_access_control.signals.access_changed.send(
            sender=PrivilegeBase, users=users, resources=resources)
    else:
        return (users, resources)


@receiver(hs_access_control.signals.access_changed, sender=PrivilegeBase)
def access_changed(sender, **kwargs):
    for username in kwargs['users']:
        user = User.objects.get(username=username)
        refresh_minio_policy(user)
    logger.info("access_changed: users: {} resources: {}".format(kwargs['users'], kwargs['resources']))

import subprocess
def admin_policy_create(target, name, file):
    arguments = ['mc', '--config-dir', '/hydroshare/', '--json', 'admin', 'policy', 'create', target, name, file]
    logger.info(arguments)
    try:
        _output = subprocess.check_output(arguments, user='hydro-service')
        logger.info(_output)
    except subprocess.CalledProcessError as e:
        logger.exception(e.output)

def admin_policy_remove(target, name):
    arguments = ['mc', '--config-dir', '/hydroshare/', '--json', 'admin', 'policy', 'remove', target, name]
    logger.info(arguments)
    try:
        _output = subprocess.check_output(arguments, user='hydro-service')
        logger.info(_output)
    except subprocess.CalledProcessError as e:
        logger.exception(e.output)

def resource_owner(resource_id: str):
    raccess = ResourceAccess.objects.filter(resource__short_id=resource_id).first()
    return raccess.first_owner.username

def create_view_statements(resource_ids: list[str]) -> list:
    view_statement_template_get = \
    {
        "Effect": "Allow",
        "Action": [
            "s3:GetBucketLocation",
            "s3:GetObject"
        ],
        "Resource": []
    }
    view_statement_template_listing = \
    {
        "Effect": "Allow",
        "Action": [
            "s3:ListBucket"
        ],
        "Resource": [],
        "Condition": {
            "StringLike": {
                "s3:prefix": []
            }
        }
    }
    get_resources = []
    list_statements = []
    for resource_id in resource_ids:
        owner = resource_owner(resource_id)
        get_resources.append(f"arn:aws:s3:::{owner}/hydroshare/{resource_id}/*")
        view_statement = copy.deepcopy(view_statement_template_listing)
        view_statement["Resource"] = [f"arn:aws:s3:::{owner}"]
        view_statement["Condition"]["StringLike"]["s3.prefix"] = [f"hydroshare/{resource_id}/*"]
        list_statements.append(view_statement)
    view_statement_template_get["Resource"] = get_resources
    return list_statements + [view_statement_template_get]


def create_edit_owner_statements(resource_ids: list[str]) -> list:
    edit_statement_template = \
    {
        "Effect": "Allow",
        "Action": [
            "s3:*"
        ],
        "Resource": []
    }
    edit_statement_template["Resource"] = [f"arn:aws:s3:::{resource_owner(resource_id)}/hydroshare/{resource_id}/*" for resource_id in resource_ids]
    return [edit_statement_template]


def minio_policy(user):
    user_privileges = user_resource_privileges(user)
    view_statements = []
    edit_statements = []
    if user_privileges["view"]:
        view_statements = create_view_statements(user_privileges["view"])
    if user_privileges["edit"] or user_privileges["owner"]:
        edit_statements = create_edit_owner_statements(user_privileges["edit"] + user_privileges["owner"])
    return \
    {
        "Version": "2012-10-17",
        "Statement": view_statements + edit_statements
    }


def refresh_minio_policy(user):
    policy = minio_policy(user)
    logger.info(json.dumps(policy, indent=2))
    if policy["Statement"]:
        with tempfile.TemporaryDirectory(dir='/hs_tmp') as tmpdirname:
            filepath = os.path.join(tmpdirname, "metadata.json")
            fp = open(filepath, "w")
            fp.write(json.dumps(policy))
            fp.close()
            admin_policy_remove(target='cuahsi', name=user.username)
            admin_policy_create(target='cuahsi', name=user.username, file=filepath)
    else:
        admin_policy_remove(target='cuahsi', name=user.username)
