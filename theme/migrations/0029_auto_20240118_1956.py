# Generated by Django 3.2.20 on 2024-01-18 19:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0028_auto_20240104_2002'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userquota',
            name='used_value',
        ),
        migrations.AddField(
            model_name='userquota',
            name='data_zone_value',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='userquota',
            name='user_zone_value',
            field=models.FloatField(default=0),
        ),
    ]
