from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group
from django.db import models
from mezzanine.pages.models import Page, RichText
from mezzanine.core.models import Ownable
from hs_core.models import AbstractResource, resource_processor
from django_docker_processes import signals
import django.dispatch
from .forms import InputForm
from hs_core.hydroshare.resource import post_create_resource
from django.utils.timezone import now
from django.dispatch import receiver
import zipfile
import ConfigParser
import cStringIO as StringIO
import os
import logging
from django.shortcuts import get_object_or_404

from hs_core.models import GenericResource

from django_docker_processes.models import DockerProfile
from django_docker_processes.models import DockerProcess

LOGGER = logging.getLogger('django')

#
# To create a new resource, use these three super-classes.
#
class InstResource(Page, RichText, AbstractResource):
    class Meta:
        verbose_name = 'RHESSys Instance Resource'
    name = models.CharField(max_length=50)
    git_repo = models.URLField()
    git_username = models.CharField(max_length=50, blank=True, null=True)
    # later change it to use Jeff's password encode function with django SECRET_KEY
    git_password = models.CharField(max_length=50, blank=True, null=True)
    commit_id = models.CharField(max_length=50)
    model_desc = models.CharField(max_length=500)
    git_branch = models.CharField(max_length=50, blank=True, null=True)
    study_area_bbox = models.CharField(max_length = 50)
    project_name = models.CharField(max_length=100)
    docker_profile = models.ForeignKey(DockerProfile, blank=True, null=True)

    def can_add(self, request):
        return AbstractResource.can_add(self, request)

    def can_change(self, request):
        return AbstractResource.can_change(self, request)

    def can_delete(self, request):
        return AbstractResource.can_delete(self, request)

    def can_view(self, request):
        return AbstractResource.can_view(self, request)

class ResourceOption(models.Model):
    class Meta:
        verbose_name ='Resource option'

    resource = models.ForeignKey(InstResource)
    name = models.CharField(max_length=64)
    value = models.CharField(max_length=4096)


def when_my_process_ends(sender, instance, result_text=None, result_data=None, result_files=None, logs=None, **kw):
    # make something out of the result data - result_data is a dict, result_text is plaintext
    # files are UploadedFile instances
    # logs are plain text stdout and stderr from the finished container
    
    # TODO filter for our type of instance
    run = get_object_or_404(ModelRun, docker_process=instance)
    owner = run.model_instance.creator

    files = result_files.values()
    LOGGER.info("Process finished, files: {0}".format(files))

    # Create resource to store results in
    from hs_core import hydroshare
    model_results = hydroshare.create_resource('GenericResource', owner, instance.profile.name + ' - ' + now().isoformat(), files=files, content=logs)

    # Save results resource to model run, update status, and end date
    run.date_finished = now()
    run.model_results = model_results
    run.status = 'Finished'
    run.save()

def when_my_process_fails(sender, instance, error_text=None, error_data=None, logs=None, **kw):
    # do something out of the error data
    # error_data is a dict
    # error_text is plain text
    # logs are plain text stdout and stderr from the dead container

    # TODO filter for our type of instance
    run = get_object_or_404(ModelRun, docker_process=instance)

    LOGGER.info('Process failed')
    if error_text:
        if instance.logs is None:
            instance.logs = ''
        instance.logs += error_text
        LOGGER.info(error_text)
    instance.save()

    # Update status, and end date
    run.date_finished = now()
    run.status = 'Error'
    run.save()


finished = signals.process_finished.connect(when_my_process_ends, weak=False)
error_handler = signals.process_aborted.connect(when_my_process_fails, weak=False)

@receiver(post_create_resource)
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

            climate_stations = md.get('rhessys', 'climate_stations')
            ResourceOption.objects.create(resource=resource,
                                          name='climate_stations',
                                          value=climate_stations)

            zfile.close()

class ModelRun(models.Model):
    class Meta:
        verbose_name = 'RHESSys Model Run'
    
    model_instance = models.ForeignKey(InstResource)
    docker_process = models.ForeignKey(DockerProcess)

    status = models.CharField(max_length=32, blank=True, null=True,
                              choices=(('Running', 'Running'),
                                       ('Finished', 'Finished'),
                                       ('Error', 'Error')))
    date_started = models.DateTimeField(auto_now_add=True)
    date_finished = models.DateTimeField(blank=True, null=True)
    model_results = models.ForeignKey(GenericResource, blank=True, null=True)

    title = models.CharField(max_length=64)
    description = models.CharField(max_length=1024, blank=True, null=True)
    model_command_line_parameters = models.CharField(max_length=1024, blank=True, null=True)

class ModelRunOptions(models.Model):
    class Meta:
        verbose_name ='Model run option'

    model_run = models.ForeignKey(ModelRun)
    name = models.CharField(max_length=64)
    value = models.CharField(max_length=4096)

