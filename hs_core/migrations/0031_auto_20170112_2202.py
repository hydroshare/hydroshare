# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_core', '0030_resourcefile_file_folder'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcefile',
            name='logical_file_content_type',
            field=models.ForeignKey(related_name='files', blank=True, on_delete=models.SET_NULL, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='resourcefile',
            name='logical_file_object_id',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
    ]
