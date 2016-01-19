# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('hs_tools_resource', '0005_remove_requesturlbase_resshortid'),
    ]

    operations = [
        migrations.CreateModel(
            name='ToolIcon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('icon', models.CharField(max_length=1024, null=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_toolicon_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='toolicon',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
