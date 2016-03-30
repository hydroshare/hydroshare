import zipfile
import ConfigParser
import cStringIO as StringIO
import os

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth.models import User, Group
from django.db import models
from django_docker_processes import signals
from django_docker_processes.models import DockerProcess
from django_docker_processes.models import DockerProfile
from django_docker_processes import tasks
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.dispatch import receiver
import django.dispatch

from mezzanine.pages.models import Page, RichText
from mezzanine.core.models import Ownable
from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor
from hs_core.signals import *
from hs_core import page_processors

from .forms import InputForm


class InstResource(BaseResource):
    objects = ResourceManager("InstResource")

    class Meta:
        verbose_name = 'RHESSys Instance Resource'
        proxy = False

    name = models.CharField(max_length=50)
    git_repo = models.URLField()
    git_username = models.CharField(max_length=50)
    # later change it to use Jeff's password encode function with django SECRET_KEY
    git_password = models.CharField(max_length=50)
    commit_id = models.CharField(max_length=50)
    model_desc = models.CharField(max_length=500)
    git_branch = models.CharField(max_length=50)
    study_area_bbox = models.CharField(max_length = 50)
    model_command_line_parameters = models.CharField(max_length=500)
    project_name = models.CharField(max_length=100)


def when_my_process_ends(sender, instance, result_text=None, result_data=None, files=None, logs=None, **kw):
    # make something out of the result data - result_data is a dict, result_text is plaintext
    # files are UploadedFile instances
    # logs are plain text stdout and stderr from the finished container
    from hs_core import hydroshare
    owner = User.objects.first() # FIXME
    hydroshare.create_resource('GenericResource', owner, instance.profile.name + ' - ' + now().isoformat(), files=files, content=logs)
    #process.delete() # no reason to leave it hanging around in the database

def when_my_process_fails(sender, instance, error_text=None, error_data=None, logs=None, **kw):
    # do something out of the error data
    # error_data is a dict
    # error_text is plain text
    # logs are plain text stdout and stderr from the dead container
    instance.logs += error_text
    instance.save()
    #process.delete() # no reason to leave it hanging around in the database

finished = signals.process_finished.connect(when_my_process_ends, weak=False)
error_handler = signals.process_aborted.connect(when_my_process_fails, weak=False)

# @receiver(pre_describe_resource, sender=InstResource)
# def rhessys_describe_resource_trigger(sender, **kwargs):
#     if(sender is InstResource):
#         files = kwargs['files']
#         if(files):
#             # Assume only one file in files, and that that file is a zipfile
#             infile = files[0]
#             infile.open('rb')
#             zfile = zipfile.ZipFile(infile)
#
#             # Get list of files in zipfile
#             zlist = zfile.namelist()
#             # Assume zipfile contains a single directory
#             root = zlist[0]
#
#             # Read metadata.txt from zipfile
#             metadataFilename = os.path.join(root, 'metadata.txt')
#
#             metadata = zfile.read(metadataFilename)
#
#             # Read metadata into ConfigParser
#             md = ConfigParser.ConfigParser()
#             md.readfp(StringIO.StringIO(metadata))
#
#             text = md.get('rhessys', 'model_description')
#             zfile.close()
#             return {"res_title": text}


@receiver(post_create_resource, sender=InstResource)
def rhessys_post_trigger(sender, **kwargs):
    if sender is InstResource:
        resource = kwargs['resource']
        files = resource.files.all()
        if(files):
            # Assume only one file in files, and that that file is a zipfile
            infile = files[0].resource_file
            infile.open('rb')
            zfile = zipfile.ZipFile(infile)

            # Get list of files in zipfile
            zlist = zfile.namelist()
            # Assume zipfile contains a single directory
            root = zlist[0]

            # Read metadata.txt from zipfile
            metadataFilename = os.path.join(root, 'metadata.txt')

            metadata = zfile.read(metadataFilename)

            # Read metadata into ConfigParser
            md = ConfigParser.ConfigParser()
            md.readfp(StringIO.StringIO(metadata))

            resource.project_name = root

            resource.model_desc = md.get('rhessys', 'model_description')

            resource.git_repo = md.get('rhessys', 'rhessys_src')

            resource.commit_id = md.get('rhessys', 'rhessys_sha')

            resource.study_area_bbox = md.get('study_area', 'bbox_wgs84')
            resource.save()
            zfile.close()

processor_for(InstResource)(resource_processor)

@processor_for(InstResource)
def main_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)
    context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None, request=request)
    extended_metadata_exists = False
    context['extended_metadata_exists'] = extended_metadata_exists
    if(request.method == 'POST'):
        form = InputForm(request.POST)
        if(form.is_valid()):
            content_model.name=form.cleaned_data['name']
            content_model.git_username = form.cleaned_data['git_username']
            content_model.git_password = form.cleaned_data['git_password']
            content_model.git_branch = form.cleaned_data['git_branch']
            content_model.model_command_line_parameters = form.cleaned_data['model_command_line_parameters']
            #content_model.project_name = form.cleaned_data['project_name']
            #content_model.model_desc = form.cleaned_data['model_desc']
            #content_model.study_area_bbox = form.cleaned_data['study_area_bbox']
            #content_model.git_repo = form.cleaned_data['git_repo']
            #content_model.commit_id = form.cleaned_data['commit_id']
            content_model.save()
            input_url = content_model.bags.first().bag.url
            env_dict = {'INPUT_URL':input_url}
            my_profile = get_object_or_404(DockerProfile, name='RHESSys_Docker_Profile')
            #my_profile = get_object_or_404(DockerProfile, name='Pandoc')
            #global process
            process = DockerProcess.objects.create(profile=my_profile) # creates a unique ID
            #promise = tasks.run_process.delay(process, **env_dict)
            promise = tasks.run_process.apply_async(args=[process, {}], **env_dict)
            logs = promise.get()
            print logs
            process.delete() # no reason to leave it hanging around in the database
    else:
        form = InputForm(initial={
            'project_name' : content_model.project_name,
            'model_desc' : content_model.model_desc,
            'git_repo' : content_model.git_repo,
            'commit_id' : content_model.commit_id,
            'study_area_bbox' : content_model.study_area_bbox
        })
    context['form'] = form
    return  context
