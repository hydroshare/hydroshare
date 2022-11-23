# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('hs_tracking', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visitor',
            name='user',
            field=models.ForeignKey(null=True, blank=True, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL, unique=True),
        ),
    ]
