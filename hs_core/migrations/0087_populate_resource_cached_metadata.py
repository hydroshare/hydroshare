import logging
from django.core.management import call_command
from django.db import migrations


logger = logging.getLogger(__name__)


def populate_resource_cached_metadata(apps, schema_editor):
    try:
        call_command('refresh_resource_cached_metadata', '--verbose', '--no-prompt')
    except Exception as e:
        logger.error(f"Error populating resource cached metadata: {str(e)}")


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0086_baseresource_cached_metadata'),
    ]

    operations = [
        migrations.RunPython(populate_resource_cached_metadata, migrations.RunPython.noop),
    ]
