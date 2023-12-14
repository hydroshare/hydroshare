# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('hs_tools_resource', '0013_auto_20171023_1724'),
    ]

    operations = [
        migrations.CreateModel(
            name='HelpPageUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(default='', max_length=1024, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_helppageurl_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='IssuesPageUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(default='', max_length=1024, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_issuespageurl_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='MailingListUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(default='', max_length=1024, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_mailinglisturl_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='Roadmap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.TextField(default='', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_roadmap_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='SourceCodeUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(default='', max_length=1024, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_sourcecodeurl_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='TestingProtocolUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(default='', max_length=1024, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_tools_resource_testingprotocolurl_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='testingprotocolurl',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='sourcecodeurl',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='roadmap',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='mailinglisturl',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='issuespageurl',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='helppageurl',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
