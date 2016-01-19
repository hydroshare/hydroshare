# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def delete_duplicates(apps, schema_editor): 
    # delete oldest copies of records from UserResourceLabels
    UserResourceLabels = apps.get_model("hs_labels", "UserResourceLabels")
    oldrecord = None 
    # order by reverse start so that the first object should be preserved
    for record in list(UserResourceLabels.objects.all()\
        .order_by("user", "resource", "label", "-start")):
        # since these are pointer comparisons, no access to models is needed
        if (oldrecord is not None 
        and oldrecord.user==record.user
        and oldrecord.resource==record.resource 
        and oldrecord.label==record.label): 
            record.delete() 
        else: 
            oldrecord = record

    # delete oldest copies of records from UserResourceFlags
    UserResourceFlags = apps.get_model("hs_labels", "UserResourceFlags")
    oldrecord = None 
    # order by reverse start so that the first object should be preserved
    for record in list(UserResourceFlags.objects.all()\
        .order_by("user", "resource", "kind", "-start")): 
        # since these are pointer comparisons, no access to models is needed
        if (oldrecord is not None 
            and oldrecord.user==record.user
            and oldrecord.resource==record.resource 
            and oldrecord.kind==record.kind): 
            record.delete() 
        else: 
            oldrecord = record


class Migration(migrations.Migration): 

    dependencies = [
        ('hs_labels', '0002_custom_migration'),
    ]

    operations = [
        migrations.RunPython(delete_duplicates), 
    ]
