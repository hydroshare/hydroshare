# Generated by Django 3.2.20 on 2024-02-01 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0032_alter_userquota_grace_period_ends'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quotamessage',
            name='enforce_content_prepend',
            field=models.TextField(default='You can not take further action because you have exceeded your quota. Your quota for HydroShare resources is {allocated}{unit}. You currently have resources that consume {used}{unit}, {percent}% of your quota. '),
        ),
        migrations.AlterField(
            model_name='quotamessage',
            name='grace_period_content_prepend',
            field=models.TextField(default='You have exceeded your HydroShare quota. Your quota for HydroShare resources is {allocated}{unit}. You currently have resources that consume {used}{unit}, {percent}% of your quota. You have a grace period until {cut_off_date} to reduce your use to below your quota, or to acquire additional quota, after which you will no longer be able to create new resources in HydroShare. '),
        ),
        migrations.AlterField(
            model_name='quotamessage',
            name='warning_content_prepend',
            field=models.TextField(default='Your quota for HydroShare resources is {allocated}{unit}. You currently have resources that consume {used}{unit}, {percent}% of your quota. Once your quota reaches 100% you will no longer be able to create new resources in HydroShare. '),
        ),
    ]