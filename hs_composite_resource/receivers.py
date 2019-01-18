import os

from django.dispatch import receiver

from hs_core.signals import pre_add_files_to_resource

from .models import CompositeResource


@receiver(pre_add_files_to_resource, sender=CompositeResource)
def pre_add_files_to_resource_handler(sender, **kwargs):
    """validates if the file can be uploaded at the specified *folder* """
    resource = kwargs['resource']
    file_folder = kwargs['folder']
    validate_files = kwargs['validate_files']
    if file_folder is not None:
        base_path = os.path.join(resource.root_path, 'data', 'contents')
        tgt_path = os.path.join(base_path, file_folder)
        if not resource.can_add_files(target_full_path=tgt_path):
            validate_files['are_files_valid'] = False
            validate_files['message'] = "Adding files to this folder is not allowed."
