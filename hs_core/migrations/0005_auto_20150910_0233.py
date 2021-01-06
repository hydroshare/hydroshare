# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0004_auto_20150721_1125'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='baseresource',
            name='discoverable',
        ),
        migrations.RemoveField(
            model_name='baseresource',
            name='do_not_distribute',
        ),
        migrations.RemoveField(
            model_name='baseresource',
            name='edit_groups',
        ),
        migrations.RemoveField(
            model_name='baseresource',
            name='edit_users',
        ),
        migrations.RemoveField(
            model_name='baseresource',
            name='frozen',
        ),
        migrations.RemoveField(
            model_name='baseresource',
            name='owners',
        ),
        migrations.RemoveField(
            model_name='baseresource',
            name='public',
        ),
        migrations.RemoveField(
            model_name='baseresource',
            name='published_and_frozen',
        ),
        migrations.RemoveField(
            model_name='baseresource',
            name='view_groups',
        ),
        migrations.RemoveField(
            model_name='baseresource',
            name='view_users',
        ),
    ]
