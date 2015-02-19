# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ref_ts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='method',
            name='content_type',
            field=models.ForeignKey(related_name='ref_ts_method_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='qualitycontrollevel',
            name='content_type',
            field=models.ForeignKey(related_name='ref_ts_qualitycontrollevel_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reftimeseries',
            name='content',
            field=models.TextField(),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='site',
            name='content_type',
            field=models.ForeignKey(related_name='ref_ts_site_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='variable',
            name='content_type',
            field=models.ForeignKey(related_name='ref_ts_variable_related', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
    ]
