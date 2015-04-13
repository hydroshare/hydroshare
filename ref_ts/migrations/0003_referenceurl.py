# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('ref_ts', '0002_auto_20150310_1927'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReferenceURL',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(max_length=500)),
                ('type', models.CharField(max_length=4)),
                ('content_type', models.ForeignKey(related_name='ref_ts_referenceurl_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
