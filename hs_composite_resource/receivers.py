# coding=utf-8
from django.dispatch import receiver

from hs_core.signals import post_add_files_to_resource, post_create_resource, \
    post_delete_file_from_resource

from .models import CompositeResource
from hs_file_types.models import GenericLogicalFile


@receiver(post_create_resource, sender=CompositeResource)
def post_create_resource_handler(sender, **kwargs):
    # create a GenericLogicalFile object for each of the
    # content files in this new resource just created
    resource = kwargs['resource']
    _set_genericlogicalfile_type(resource)


@receiver(post_add_files_to_resource, sender=CompositeResource)
def post_add_files_to_resource_handler(sender, **kwargs):
    """sets GenericLogicalFile type to any file that is not already part of any logical file"""
    resource = kwargs['resource']
    _set_genericlogicalfile_type(resource)


@receiver(post_delete_file_from_resource, sender=CompositeResource)
def post_delete_file_from_resource_handler(sender, **kwargs):
    """resource lavel coverage data needs to be updated when a content file
    gets deleted from composite resource"""
    from hs_file_types.utils import update_resource_coverage_element
    resource = kwargs['resource']
    update_resource_coverage_element(resource)


def _set_genericlogicalfile_type(resource):
    """sets GenericLogicalFile type to any file that is not already part of any logical file
    in the specified resource
    """
    for res_file in resource.files.all():
        if not res_file.has_logical_file:
            logical_file = GenericLogicalFile.create()
            res_file.logical_file_content_object = logical_file
            res_file.save()
