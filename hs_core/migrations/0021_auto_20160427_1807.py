# -*- coding: utf-8 -*-


from django.db import migrations, models
import django_s3.storage
import hs_core.models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0020_baseresource_collections'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcefile',
            name='fed_resource_file_name_or_path',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='resourcefile',
            name='resource_file',
            field=models.FileField(storage=django_s3.storage.S3Storage(), max_length=500, null=True, upload_to=hs_core.models.get_path, blank=True),
        ),
    ]
