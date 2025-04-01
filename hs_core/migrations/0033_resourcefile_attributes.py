# -*- coding: utf-8 -*-


from django.db import migrations, models
import django_s3.storage
import hs_core.models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0032_auto_20170120_1445'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcefile',
            name='fed_resource_file',
            field=models.FileField(storage=hs_core.models.S3Storage(), max_length=4096, null=True, upload_to=hs_core.models.get_path, blank=True),
        ),
        migrations.AlterField(
            model_name='resourcefile',
            name='file_folder',
            field=models.CharField(max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='resourcefile',
            name='resource_file',
            field=models.FileField(storage=django_s3.storage.S3Storage(), max_length=4096, null=True, upload_to=hs_core.models.get_path, blank=True),
        ),
    ]
