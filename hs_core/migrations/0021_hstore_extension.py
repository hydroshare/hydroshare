

from django.db import models, migrations
from django.contrib.postgres.operations import HStoreExtension


class Migration(migrations.Migration):

    dependencies = [
            ('hs_core', '0020_baseresource_collections'),
    ]

    operations = [

        HStoreExtension(),

    ]
