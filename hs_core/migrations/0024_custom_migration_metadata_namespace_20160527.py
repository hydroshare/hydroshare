from __future__ import unicode_literals

import logging

from django.db import migrations

from hs_core.models import BaseResource
from hs_core.hydroshare.utils import resource_modified

def migrate_namespace_for_source_and_relation(apps, schema_editor):
    # migrate the namespace for the 'Source' and 'Relation' metadata
    # elements from 'dcterms' to 'hsterms' by regenerating the metadata xml
    log = logging.getLogger()
    for res in BaseResource.objects.all():
        # need to regenerate xml file only for those resources that have either 'source' or 'relation' metadata
        if len(res.metadata.sources.all()) > 0 or len(res.metadata.relations.all()) > 0:
            resource_modified(res, res.creator)
            log_msg = "Namespace for either 'source' or 'relation' metadata element was updated for resource " \
                      "with ID:{} and type:{}."
            log_msg = log_msg.format(res.short_id, res.resource_type)
            log.info(log_msg)
            # TODO: after debugging remove the print
            print (log_msg)


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0023_merge'),
    ]

    operations = [
        migrations.RunPython(code=migrate_namespace_for_source_and_relation),
    ]