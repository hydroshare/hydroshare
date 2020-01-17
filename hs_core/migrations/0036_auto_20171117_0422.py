# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0035_remove_deprecated_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='contributor',
            name='identifiers',
            field=django.contrib.postgres.fields.hstore.HStoreField(default={}),
        ),
        migrations.AddField(
            model_name='creator',
            name='identifiers',
            field=django.contrib.postgres.fields.hstore.HStoreField(default={}),
        ),
    ]
