# Generated by Django 3.2.19 on 2023-09-29 20:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0076_resource_file_unique_constraint'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='spam_allowlisted',
            field=models.BooleanField(default=False),
        ),
    ]
