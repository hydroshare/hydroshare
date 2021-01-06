# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0004_auto_20150721_1125'),
        ('hs_geo_raster_resource', '0002_auto_20150813_1313'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rasterresource',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='creator',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='edit_groups',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='edit_users',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='last_changed_by',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='owners',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='user',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='view_groups',
        ),
        migrations.RemoveField(
            model_name='rasterresource',
            name='view_users',
        ),
        migrations.DeleteModel(
            name='RasterResource',
        ),
        migrations.CreateModel(
            name='RasterResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Geographic Raster',
                'proxy': True,
            },
            bases=('hs_core.genericresource',),
        ),
    ]
