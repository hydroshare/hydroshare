# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_collection_resource', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collection',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='resources',
        ),
        migrations.RemoveField(
            model_name='collectionmetadata',
            name='coremetadata_ptr',
        ),
        migrations.DeleteModel(
            name='Collection',
        ),
        migrations.DeleteModel(
            name='CollectionMetaData',
        ),
    ]
