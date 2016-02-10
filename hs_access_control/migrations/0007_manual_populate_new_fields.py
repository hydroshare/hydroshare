# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def move_access_data(apps, schema_editor): 

    UserGroupPrivilege = apps.get_model('hs_access_control', 'UserGroupPrivilege') 
    for ugp in UserGroupPrivilege.objects.all(): 
        ugp.usernew = ugp.user.user 
        ugp.groupnew = ugp.group.group
        ugp.grantornew = ugp.grantor.user 
        ugp.save()
        
    UserResourcePrivilege = apps.get_model('hs_access_control', 'UserResourcePrivilege') 
    for urp in UserResourcePrivilege.objects.all(): 
        urp.usernew = urp.user.user 
        urp.resourcenew = urp.resource.resource
        urp.grantornew = urp.grantor.user 
        urp.save()

    GroupResourcePrivilege = apps.get_model('hs_access_control', 'GroupResourcePrivilege') 
    for grp in GroupResourcePrivilege.objects.all(): 
        grp.usernew = grp.user.user 
        grp.groupnew = grp.group.group
        grp.grantornew = grp.grantor.user 
        grp.save()

class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0006_auto_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(move_access_data)
    ]
