# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_tools_resource', '0007_auto_20160122_2240'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportedSharingStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_supportedsharingstatus_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SupportedSharingStatusChoices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=128)),
            ],
        ),
        migrations.AddField(
            model_name='supportedsharingstatus',
            name='sharing_status',
            field=models.ManyToManyField(to='hs_tools_resource.SupportedSharingStatusChoices', null=True, blank=True),
        ),
    ]
