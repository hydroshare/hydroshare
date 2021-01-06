# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0009_quotamessage_enforce_quota'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userquota',
            name='zone',
            field=models.CharField(default='hydroshare', max_length=100),
        ),
    ]
