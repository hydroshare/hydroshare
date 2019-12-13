# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_file_types', '0006_auto_20170812_1621'),
    ]

    operations = [
        migrations.AddField(
            model_name='reftimeseriesfilemetadata',
            name='abstract',
            field=models.TextField(null=True, blank=True),
        ),
    ]
