import os

from django.dispatch import receiver

from hs_core.signals import pre_add_files_to_resource, pre_check_bag_flag

from .models import CompositeResource


@receiver(pre_add_files_to_resource, sender=CompositeResource)
def pre_add_files_to_resource_handler(sender, **kwargs):
    """validates if the file can be uploaded at the specified *folder* """
    resource = kwargs['resource']
    file_folder = kwargs['folder']
    validate_files = kwargs['validate_files']
    if file_folder:
        base_path = os.path.join(resource.root_path, 'data', 'contents')
        tgt_path = os.path.join(base_path, file_folder)
        if not resource.can_add_files(target_full_path=tgt_path):
            validate_files['are_files_valid'] = False
            validate_files['message'] = "Adding files to this folder is not allowed."


@receiver(pre_check_bag_flag, sender=CompositeResource)
def pre_check_bag_flag_handler(sender, **kwargs):
    """
    Regenerate xml files for any model instance aggregation that may have link to external model program aggregation
    """
    resource = kwargs['resource']
    has_external_mp = False
    if resource.raccess.published and 'EXECUTED_BY_RES_ID' in resource.extra_data:
        for lf in resource.modelinstancelogicalfile_set.all():
            if lf.metadata.executed_by:
                mp_aggr_resource = lf.metadata.executed_by.resource
                if resource.short_id != mp_aggr_resource.short_id:
                    has_external_mp = True
                    lf.create_aggregation_xml_documents(create_map_xml=False)
            else:
                lf.create_aggregation_xml_documents(create_map_xml=False)

        if not has_external_mp:
            resource.extra_data.pop('EXECUTED_BY_RES_ID')
            resource.save()
