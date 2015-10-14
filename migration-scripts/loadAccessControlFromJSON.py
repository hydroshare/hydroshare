# usage: python loadAccessControlFromJSON.py resources.JSON
# where resources.JSON has old resource info including access controls.
# This script read the old resource access control info and ingest
# them into the new access control system
# Author: Hong Yi
import os
import sys
import json

os.environ.setdefault("PYTHONPATH", '/home/docker/hydroshare')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hydroshare.settings'

import django
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

django.setup()

from hs_core import hydroshare
from hs_access_control.models import PrivilegeCodes, HSAccessException

with open(sys.argv[1]) as old_res_file:
    # cannot use django serializers.deserialize("json", old_res_file) since the new resource model
    # has changed which will result in "no field" errors while loading old resource data into new
    # resource model; instead, directly read json data to get access control data to ingest back
    # into new resource model
    res_data = json.loads(old_res_file.read())
    for item in res_data:
        res_id = item["fields"]["short_id"]
        owners = item["fields"]["owners"]
        edit_users = item["fields"]["edit_users"]
        view_users = item["fields"]["view_users"]

        owner_user_objs = User.objects.in_bulk(owners).values()
        edit_user_objs = User.objects.in_bulk(edit_users).values()
        view_user_objs = User.objects.in_bulk(view_users).values()

        try:
           res = hydroshare.utils.get_resource_by_shortkey(res_id, or_404=False)
        except ObjectDoesNotExist:
           print "No resource was found for resource id:%s" % res_id
           continue

        isPublic = item["fields"]["public"]
        if isPublic:
            res.raccess.public = True
            res.raccess.discoverable = True
            res.raccess.save()

        res_creator = res.creator

        for view_user in view_user_objs:
            try:
                res_creator.uaccess.share_resource_with_user(res, view_user, PrivilegeCodes.VIEW)
            except HSAccessException as exp:
                print exp.message
                old_res_file.close()
                sys.exit()

        for edit_user in edit_user_objs:
            try:
                res_creator.uaccess.share_resource_with_user(res, edit_user, PrivilegeCodes.CHANGE)
            except HSAccessException as exp:
                print exp.message
                old_res_file.close()
                sys.exit()

        for owner_user in owner_user_objs:
            try:
                res_creator.uaccess.share_resource_with_user(res, owner_user, PrivilegeCodes.OWNER)
            except HSAccessException as exp:
                print exp.message
                old_res_file.close()
                sys.exit()

        # check whether the initial res_creator is in owner_user_objs list, and remove it if not
        if not res_creator in owner_user_objs:
            res_creator.uaccess.unshare_resource_with_user(res, res_creator)
            res.creator = owner_user_objs[0]
            res.last_changed_by = owner_user_objs[0]
            res.save()

        # delete admin from creators and contributors metadata elements to remove artifacts triggered
        # by bag ingestion code for resources with all creators being non-HydroShare users
        admin_creator = res.metadata.creators.filter(name='HydroShare (Admin)').first()
        if admin_creator:
            res.metadata.delete_element('creator', admin_creator.id)
        admin_contributor = res.metadata.contributors.filter(name='HydroShare (Admin)').first()
        if admin_contributor:
            res.metadata.delete_element('contributor', admin_contributor.id)

        # double make sure admin is indeed replaced by the first owner of the resource in case there is some issue with previoius calls
        if res.creator.username == 'admin':
            res.creator = owner_user_objs[0]
            res.last_changed_by = owner_user_objs[0]
            res.save()

    old_res_file.close()