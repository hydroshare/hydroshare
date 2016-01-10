# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def move_access_data(apps, schema_editor): 

    UserGroupPrivilege = apps.get_model('hs_access_control', 'UserGroupPrivilege') 
    for ugp in UserGroupPrivilege.objects.all(): 
	ugp.usernew = ugp.user.user 
        ugp.groupnew = ugp.group.group
	ugp.grantornew = ugp.grantor.user 
    
    UserResourcePrivilege = apps.get_model('hs_access_control', 'UserResourcePrivilege') 
    for urp in UserResourcePrivilege.objects.all(): 
	urp.usernew = urp.user.user 
        urp.resourcenew = urp.resource.resource
	urp.grantornew = urp.grantor.user 

    GroupResourcePrivilege = apps.get_model('hs_access_control', 'GroupResourcePrivilege') 
    for ugp in GroupResourcePrivilege.objects.all(): 
	ugp.usernew = ugp.user.user 
        ugp.groupnew = ugp.group.group
	ugp.grantornew = ugp.grantor.user 

class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0006_add_new_fields'),
    ]

    operations = [
	migrations.RunPython(move_access_data)
    ]
