# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_tools_resource', '0008_auto_20160729_1811'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppHomePageUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(max_length=1024, null=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_apphomepageurl_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='apphomepageurl',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
