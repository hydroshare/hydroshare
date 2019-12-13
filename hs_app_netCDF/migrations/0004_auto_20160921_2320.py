# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_app_netCDF', '0003_netcdfresource'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variable',
            name='descriptive_name',
            field=models.CharField(max_length=1000, null=True, verbose_name='long name', blank=True),
        ),
        migrations.AlterField(
            model_name='variable',
            name='missing_value',
            field=models.CharField(max_length=1000, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='variable',
            name='name',
            field=models.CharField(max_length=1000),
        ),
        migrations.AlterField(
            model_name='variable',
            name='shape',
            field=models.CharField(max_length=1000),
        ),
        migrations.AlterField(
            model_name='variable',
            name='type',
            field=models.CharField(max_length=1000, choices=[('Char', 'Char'), ('Byte', 'Byte'), ('Short', 'Short'), ('Int', 'Int'), ('Float', 'Float'), ('Double', 'Double'), ('Int64', 'Int64'), ('Unsigned Byte', 'Unsigned Byte'), ('Unsigned Short', 'Unsigned Short'), ('Unsigned Int', 'Unsigned Int'), ('Unsigned Int64', 'Unsigned Int64'), ('String', 'String'), ('User Defined Type', 'User Defined Type'), ('Unknown', 'Unknown')]),
        ),
        migrations.AlterField(
            model_name='variable',
            name='unit',
            field=models.CharField(max_length=1000),
        ),
    ]
