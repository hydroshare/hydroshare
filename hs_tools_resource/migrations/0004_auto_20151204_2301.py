# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('hs_tools_resource', '0003_auto_20150724_1501'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportedResTypeChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=128)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SupportedResTypes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_supportedrestypes_related', to='contenttypes.ContentType')),
                ('supported_res_types', models.ManyToManyField(to='hs_tools_resource.SupportedResTypeChoices', null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='fee',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='Fee',
        ),
        migrations.RemoveField(
            model_name='toolresourcetype',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='ToolResourceType',
        ),
        migrations.AlterModelOptions(
            name='toolresource',
            options={'ordering': ('_order',), 'verbose_name': 'Web App Resource'},
        ),
        migrations.AddField(
            model_name='requesturlbase',
            name='resShortID',
            field=models.CharField(default=b'UNKNOWN', max_length=128),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='requesturlbase',
            name='value',
            field=models.CharField(max_length=1024, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='toolversion',
            name='value',
            field=models.CharField(default=b'1.0', max_length=128),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='requesturlbase',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='toolversion',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
