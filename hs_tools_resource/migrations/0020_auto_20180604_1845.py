# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_tools_resource', '0019_auto_20180531_2304'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequestUrlBaseAggregation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(default=b'', max_length=1024, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_requesturlbaseaggregation_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='RequestUrlBaseFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(default=b'', max_length=1024, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_requesturlbasefile_related', to='contenttypes.ContentType')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='requesturlbasefile',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='requesturlbaseaggregation',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
