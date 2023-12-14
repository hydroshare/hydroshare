# -*- coding: utf-8 -*-


from django.db import models, migrations
import mezzanine.core.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('pages', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HomePage',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, on_delete=models.CASCADE, to='pages.Page')),
                ('heading', models.CharField(max_length=100)),
                ('slide_in_one_icon', models.CharField(max_length=50, blank=True)),
                ('slide_in_one', models.CharField(max_length=200, blank=True)),
                ('slide_in_two_icon', models.CharField(max_length=50, blank=True)),
                ('slide_in_two', models.CharField(max_length=200, blank=True)),
                ('slide_in_three_icon', models.CharField(max_length=50, blank=True)),
                ('slide_in_three', models.CharField(max_length=200, blank=True)),
                ('header_background', mezzanine.core.fields.FileField(max_length=255, verbose_name='Header Background', blank=True)),
                ('header_image', mezzanine.core.fields.FileField(max_length=255, null=True, verbose_name='Header Image (optional)', blank=True)),
                ('welcome_heading', models.CharField(default='Welcome', max_length=100)),
                ('content', mezzanine.core.fields.RichTextField()),
                ('recent_blog_heading', models.CharField(default='Latest blog posts', max_length=100)),
                ('number_recent_posts', models.PositiveIntegerField(default=3, help_text='Number of recent blog posts to show')),
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Home page',
                'verbose_name_plural': 'Home pages',
            },
            bases=('pages.page',),
        ),
        migrations.CreateModel(
            name='IconBox',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('_order', models.IntegerField(null=True, verbose_name='Order')),
                ('icon', models.CharField(help_text='Enter the name of a font awesome icon, i.e. fa-eye. A list is available here http://fontawesome.io/', max_length=50)),
                ('title', models.CharField(max_length=200)),
                ('link_text', models.CharField(max_length=100)),
                ('link', models.CharField(help_text='Optional, if provided clicking the box will go here.', max_length=2000, blank=True)),
                ('homepage', models.ForeignKey(related_name='boxes', on_delete=models.CASCADE, to='theme.HomePage')),
            ],
            options={
                'ordering': ('_order',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SiteConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('col1_heading', models.CharField(default='Contact us', max_length=200)),
                ('col1_content', mezzanine.core.fields.RichTextField()),
                ('col2_heading', models.CharField(default='Follow', max_length=200)),
                ('col2_content', mezzanine.core.fields.RichTextField(help_text='If present will override the social network icons.', blank=True)),
                ('col3_heading', models.CharField(default='Subscribe', max_length=200)),
                ('col3_content', mezzanine.core.fields.RichTextField()),
                ('twitter_link', models.CharField(max_length=2000, blank=True)),
                ('facebook_link', models.CharField(max_length=2000, blank=True)),
                ('pinterest_link', models.CharField(max_length=2000, blank=True)),
                ('youtube_link', models.CharField(max_length=2000, blank=True)),
                ('github_link', models.CharField(max_length=2000, blank=True)),
                ('linkedin_link', models.CharField(max_length=2000, blank=True)),
                ('vk_link', models.CharField(max_length=2000, blank=True)),
                ('gplus_link', models.CharField(max_length=2000, blank=True)),
                ('has_social_network_links', models.BooleanField(default=False)),
                ('copyright', models.TextField(default='&copy {% now "Y" %} {{ settings.SITE_TITLE }}')),
                ('site', models.ForeignKey(editable=False, on_delete=models.CASCADE, to='sites.Site')),
            ],
            options={
                'verbose_name': 'Site Configuration',
                'verbose_name_plural': 'Site Configuration',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('picture', models.ImageField(null=True, upload_to='profile', blank=True)),
                ('title', models.CharField(help_text='e.g. Assistant Professor, Program Director, Adjunct Professor, Software Developer.', max_length=1024, null=True, blank=True)),
                ('profession', models.CharField(default='Student', max_length=1024, null=True, help_text='e.g. Student, Researcher, Research Faculty, Research Staff, Project Manager, Teacher, Research Assistant.', blank=True)),
                ('subject_areas', models.CharField(help_text='A comma-separated list of subject areas you are interested in researching. e.g. "Computer Science, Hydrology, Water Management"', max_length=1024, null=True, blank=True)),
                ('organization', models.CharField(help_text='The name of the organization you work for.', max_length=1024, null=True, blank=True)),
                ('organization_type', models.CharField(blank=True, max_length=1024, null=True, choices=[('Higher Education', 'Higher Education'), ('Research', 'Research'), ('Government', 'Government'), ('Commercial', 'Commercial'), ('Primary Education', 'Primary Education'), ('Secondary Education', 'Secondary Education')])),
                ('phone_1', models.CharField(max_length=1024, null=True, blank=True)),
                ('phone_1_type', models.CharField(blank=True, max_length=1024, null=True, choices=[('Home', 'Home'), ('Work', 'Work'), ('Mobile', 'Mobile')])),
                ('phone_2', models.CharField(max_length=1024, null=True, blank=True)),
                ('phone_2_type', models.CharField(blank=True, max_length=1024, null=True, choices=[('Home', 'Home'), ('Work', 'Work'), ('Mobile', 'Mobile')])),
                ('public', models.BooleanField(default=True, help_text='Uncheck to make your profile contact information and details private.')),
                ('cv', models.FileField(help_text='Upload your Curriculum Vitae if you wish people to be able to download it.', null=True, upload_to='profile', blank=True)),
                ('details', models.TextField(help_text='Tell the HydroShare community a little about yourself.', null=True, verbose_name='Description', blank=True)),
                ('user', models.OneToOneField(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
