from __future__ import unicode_literals

from django.db import migrations
from django.contrib.auth.models import User

from hs_core.models import BaseResource
from hs_labels.models import UserLabels, ResourceLabels


def migrate_users_and_resources(apps, schema_editor):
    # create a 'UserLabel' record for each existing user - needed for the new resource labelling
    UserLabels.objects.all().delete()
    for u in User.objects.all():
        ul = UserLabels(user=u)
        ul.save()
    # create a 'ResourceLabel' record for each existing Resource - needed for the new resource labelling
    ResourceLabels.objects.all().delete()
    for r in BaseResource.objects.all():
        rl = ResourceLabels(resource=r)
        rl.save()


def undo_migrate_users_and_resources(apps, schema_editor):
    UserLabels.objects.all().delete()

    ResourceLabels.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hs_labels', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(code=migrate_users_and_resources, reverse_code=undo_migrate_users_and_resources),
    ]
