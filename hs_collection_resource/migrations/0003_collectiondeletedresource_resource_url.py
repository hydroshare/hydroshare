# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from hs_core.hydroshare.utils import current_site_url


def initial_value(apps, schema_editor):
    CollectionDeletedResource = apps.get_model('hs_collection_resource', 'CollectionDeletedResource')
    for o in CollectionDeletedResource.objects.all():
        o.resource_url = current_site_url('/resource/{}'.format(o.resource_id))
        o.save()


class Migration(migrations.Migration):

    dependencies = [
        ('hs_collection_resource', '0002_collectiondeletedresource_resource_owners'),
    ]

    operations = [
        migrations.AddField(
            model_name='collectiondeletedresource',
            name='resource_url',
            field=models.CharField(default='', max_length=2000),
            preserve_default=False,
        ),
    ]
