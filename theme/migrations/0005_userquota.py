# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('theme', '0004_userprofile_create_irods_user_account'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserQuota',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('allocated_value', models.BigIntegerField(default=20)),
                ('used_value', models.BigIntegerField(default=0)),
                ('unit', models.CharField(default='G', max_length=10)),
                ('zone', models.CharField(default='hydroshare_internal', max_length=100)),
                ('remaining_grace_period', models.IntegerField(default=-1)),
                ('user', models.ForeignKey(related_query_name='quotas', related_name='quotas', editable=False, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User quota',
                'verbose_name_plural': 'User quotas',
            },
        ),
        migrations.AlterUniqueTogether(
            name='userquota',
            unique_together=set([('user', 'zone')]),
        ),
        migrations.CreateModel(
            name='QuotaMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('warning_content_prepend', models.TextField(
                    default='Your quota for HydroShare resources is {allocated}{unit} in {zone} zone. You currently have resources that consume {used}{unit}, {percent}% of your quota. Once your quota reaches 100% you will no longer be able to create new resources in HydroShare. ')),
                ('grace_period_content_prepend', models.TextField(
                    default='You have exceeded your HydroShare quota. Your quota for HydroShare resources is {allocated}{unit} in {zone} zone. You currently have resources that consume {used}{unit}, {percent}% of your quota. You have a grace period until {cut_off_date} to reduce your use to below your quota, or to acquire additional quota, after which you will no longer be able to create new resources in HydroShare. ')),
                ('enforce_content_prepend', models.TextField(
                    default='Your action was refused because you have exceeded your quota. Your quota for HydroShare resources is {allocated}{unit} in {zone} zone. You currently have resources that consume {used}{unit}, {percent}% of your quota. ')),
                ('content', models.TextField(
                    default='To request additional quota, please contact help@cuahsi.org. We will try to accommodate reasonable requests for additional quota. If you have a large quota request you may need to contribute toward the costs of providing the additional space you need. See https://help.hydroshare.org/about-hydroshare/policies/quota/ for more information about the quota policy.')),
                ('soft_limit_percent', models.IntegerField(default=80)),
                ('hard_limit_percent', models.IntegerField(default=125)),
                ('grace_period', models.IntegerField(default=7)),
            ],
        ),
    ]
