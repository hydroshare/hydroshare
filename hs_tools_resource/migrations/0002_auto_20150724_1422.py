# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tools_resource', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='toolresource',
            options={'ordering': ('_order',), 'verbose_name': 'Old Tool Resource'},
        ),
        migrations.AlterModelTable(
            name='toolresource',
            table='hs_tools_resource_toolresource',
        ),
    ]
