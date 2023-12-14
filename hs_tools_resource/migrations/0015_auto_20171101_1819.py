# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_tools_resource', '0014_auto_20171101_1812'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShowOnOpenWithList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.BooleanField(default=False)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_showonopenwithlist_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='showonopenwithlist',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
