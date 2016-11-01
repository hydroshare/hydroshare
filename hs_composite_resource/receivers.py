# coding=utf-8
from django.dispatch import receiver

from hs_core.signals import post_add_files_to_resource, post_create_resource

from .models import CompositeResource
from hs_file_types.models import GenericLogicalFile


@receiver(post_create_resource, sender=CompositeResource)
def post_create_resource_handler(sender, **kwargs):
    resource = kwargs['resource']
    for res_file in resource.files.all():
        if not res_file.has_logical_file:
            logical_file = GenericLogicalFile.create()
            res_file.logical_file_content_object = logical_file
            res_file.save()


@receiver(post_add_files_to_resource, sender=CompositeResource)
def post_add_files_to_resource_handler(sender, **kwargs):
    """sets GenericLogicalFile type to any file that is not already part of any logical file"""
    resource = kwargs['resource']
    for res_file in resource.files.all():
        if not res_file.has_logical_file:
            logical_file = GenericLogicalFile.create()
            res_file.logical_file_content_object = logical_file
            res_file.save()
