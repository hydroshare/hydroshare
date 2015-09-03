# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0003_auto_20150811_2213'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='genericresource',
            name='discoverable',
        ),
        migrations.RemoveField(
            model_name='genericresource',
            name='do_not_distribute',
        ),
        migrations.RemoveField(
            model_name='genericresource',
            name='edit_groups',
        ),
        migrations.RemoveField(
            model_name='genericresource',
            name='edit_users',
        ),
        migrations.RemoveField(
            model_name='genericresource',
            name='frozen',
        ),
        migrations.RemoveField(
            model_name='genericresource',
            name='owners',
        ),
        migrations.RemoveField(
            model_name='genericresource',
            name='public',
        ),
        migrations.RemoveField(
            model_name='genericresource',
            name='published_and_frozen',
        ),
        migrations.RemoveField(
            model_name='genericresource',
            name='view_groups',
        ),
        migrations.RemoveField(
            model_name='genericresource',
            name='view_users',
        ),
    ]
