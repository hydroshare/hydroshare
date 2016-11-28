# coding=utf-8
import os
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from hs_core.signals import post_add_files_to_resource, post_create_resource, \
    post_delete_file_from_resource, pre_move_or_rename_file_or_folder

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
    """resource label coverage data needs to be updated when a content file
    gets deleted from composite resource"""
    from hs_file_types.utils import update_resource_coverage_element
    resource = kwargs['resource']
    update_resource_coverage_element(resource)


@receiver(pre_move_or_rename_file_or_folder, sender=CompositeResource)
def pre_move_or_rename_file_or_folder_handler(sender, **kwargs):
    """check if file/folder rename/move is allowed
    If not allowed, raises ValidationError exception
    """

    resource = kwargs['resource']
    src_full_path = kwargs['src_full_path']
    tgt_full_path = kwargs['tgt_full_path']
    err_msg = "File/folder move/rename is not allowed."
    istorage = resource.get_irods_storage()
    tgt_file_dir = os.path.dirname(tgt_full_path)
    src_file_dir = os.path.dirname(src_full_path)

    def check_targe_directory():
        path_to_check = ''
        if istorage.exists(tgt_file_dir):
            path_to_check = tgt_file_dir
        else:
            if tgt_file_dir.startswith(src_file_dir):
                path_to_check = src_file_dir

        if path_to_check:
            if resource.resource_federation_path:
                res_file_objs = resource.files.filter(object_id=resource.id,
                                                      fed_resource_file_name_or_path__contains=
                                                      path_to_check).all()
            else:
                res_file_objs = resource.files.filter(object_id=resource.id,
                                                      resource_file__contains=
                                                      path_to_check).all()
            for res_file_obj in res_file_objs:
                if not res_file_obj.logical_file.allow_resource_file_rename or \
                        not res_file_obj.logical_file.allow_resource_file_move:
                    raise ValidationError(err_msg)

    if resource.resource_federation_path:
        res_file_obj = resource.files.filter(object_id=resource.id,
                                             fed_resource_file_name_or_path=
                                             src_full_path).first()
    else:
        res_file_obj = resource.files.filter(object_id=resource.id,
                                             resource_file=src_full_path).first()
    if res_file_obj is not None:
        # src_full_path contains file name
        if not res_file_obj.logical_file.allow_resource_file_rename or \
                not res_file_obj.logical_file.allow_resource_file_move:
            raise ValidationError(err_msg)

        # check if the target directory allows stuff to be moved there
        check_targe_directory()
    else:
        # src_full_path is a folder path without file name
        # tgt_full_path also must be a folder path without file name
        # check that if the target folder contains any files and if any of those files
        # allow moving stuff there
        check_targe_directory()


def _set_genericlogicalfile_type(resource):
    """sets GenericLogicalFile type to any file that is not already part of any logical file
    in the specified resource
    """
    for res_file in resource.files.all():
        if not res_file.has_logical_file:
            logical_file = GenericLogicalFile.create()
            res_file.logical_file_content_object = logical_file
            res_file.save()