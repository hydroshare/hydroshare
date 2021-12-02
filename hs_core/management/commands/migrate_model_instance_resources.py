import logging
import os

from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag, get_resource_by_shortkey
from hs_core.models import CoreMetaData, ResourceFile
from hs_file_types.models import ModelInstanceLogicalFile
from hs_modelinstance.models import ModelInstanceResource
from ..utils import migrate_core_meta_elements


class Command(BaseCommand):
    help = "Convert all model instance resources to composite resource with model instance aggregation"
    _EXECUTED_BY_EXTRA_META_KEY = 'EXECUTED_BY_RES_ID'

    def get_aggregation_folder_name(self, comp_res):
        # generate a folder name if the default name already exists
        default_folder_name = "model-instance"
        folder_name = default_folder_name
        istorage = comp_res.get_irods_storage()
        folder_path = os.path.join(comp_res.file_path, default_folder_name)
        post_fix = 1
        while istorage.exists(folder_path):
            folder_name = "{}-{}".format(default_folder_name, post_fix)
            folder_path = os.path.join(comp_res.file_path, folder_name)
            post_fix += 1
        return folder_name

    def move_files_and_folders_to_aggregation(self, mi_aggr, comp_res, logger):
        # create a new folder for mi aggregation to which all files and folders will be moved
        new_folder = self.get_aggregation_folder_name(comp_res)
        ResourceFile.create_folder(comp_res, new_folder, migrating_resource=True)
        mi_aggr.folder = new_folder
        mi_aggr.dataset_name = new_folder
        mi_aggr.save()
        msg = "Added a new folder '{}' to the resource:{}".format(new_folder, comp_res.short_id)
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))

        # move files and folders to the new aggregation folder
        istorage = comp_res.get_irods_storage()
        moved_folders = []

        for res_file in comp_res.files.all().iterator():
            if res_file != comp_res.readme_file:
                moving_folder = False
                if res_file.file_folder:
                    if "/" in res_file.file_folder:
                        folder_to_move = res_file.file_folder.split("/")[0]
                    else:
                        folder_to_move = res_file.file_folder
                    if folder_to_move not in moved_folders:
                        moved_folders.append(folder_to_move)
                        moving_folder = True
                    else:
                        continue
                    src_short_path = folder_to_move
                else:
                    src_short_path = res_file.file_name

                src_full_path = os.path.join(comp_res.root_path, 'data', 'contents', src_short_path)
                if istorage.exists(src_full_path):
                    tgt_full_path = os.path.join(comp_res.root_path, 'data', 'contents', new_folder, src_short_path)
                    if moving_folder:
                        msg = "Moving folder ({}) to the new aggregation folder:{}".format(src_short_path, new_folder)
                    else:
                        msg = "Moving file ({}) to the new aggregation folder:{}".format(src_short_path, new_folder)
                    self.stdout.write(msg)

                    istorage.moveFile(src_full_path, tgt_full_path)
                    if moving_folder:
                        msg = "Moved folder ({}) to the new aggregation folder:{}".format(src_short_path, new_folder)
                        logger.info(msg)
                        self.stdout.write(self.style.SUCCESS(msg))
                        self.stdout.flush()

                        res_file_objs = ResourceFile.list_folder(comp_res, folder_to_move)
                        tgt_short_path = os.path.join(new_folder, folder_to_move)
                        for fobj in res_file_objs:
                            src_path = fobj.storage_path
                            new_path = src_path.replace(folder_to_move, tgt_short_path, 1)
                            fobj.set_storage_path(new_path)
                            mi_aggr.add_resource_file(fobj)
                            msg = "Added file ({}) to model instance aggregation".format(fobj.short_path)
                            logger.info(msg)
                            self.stdout.write(self.style.SUCCESS(msg))
                    else:
                        msg = "Moved file ({}) to the new aggregation folder:{}".format(src_short_path, new_folder)
                        logger.info(msg)
                        self.stdout.write(self.style.SUCCESS(msg))
                        res_file.set_storage_path(tgt_full_path)
                        mi_aggr.add_resource_file(res_file)
                        msg = "Added file ({}) to model instance aggregation".format(res_file.short_path)
                        logger.info(msg)
                        self.stdout.write(self.style.SUCCESS(msg))
                else:
                    err_msg = "File path ({}) not found in iRODS. Couldn't make this file part of " \
                              "the model instance aggregation.".format(src_full_path)
                    logger.warn(err_msg)
                    self.stdout.write(self.style.WARNING(err_msg))
                self.stdout.flush()

    def set_executed_by(self, mi_aggr, comp_res, logger):
        linked_res_id = comp_res.extra_data[self._EXECUTED_BY_EXTRA_META_KEY]
        try:
            linked_res = get_resource_by_shortkey(linked_res_id)
        except Exception as err:
            msg = "Linked resource (ID:{}) was not found. Error:{}".format(linked_res_id, str(err))
            logger.warning(msg)
            self.stdout.write(self.style.WARNING(msg))
            self.stdout.flush()
            return

        # check the linked resource is a composite resource
        if linked_res.resource_type == 'CompositeResource':
            # get the mp aggregation
            mp_aggr = linked_res.modelprogramlogicalfile_set.first()
            if mp_aggr:
                # use the external mp aggregation for executed_by
                mi_aggr.metadata.executed_by = mp_aggr
                if mp_aggr.metadata_schema_json:
                    mi_aggr.metadata_schema_json = mp_aggr.metadata_schema_json
                    mi_aggr.save()
                mi_aggr.metadata.save()
                msg = 'Setting executed_by to external model program aggregation of resource (ID:{})'
                msg = msg.format(linked_res.short_id)
                logger.info(msg)
                self.stdout.write(self.style.SUCCESS(msg))
            else:
                msg = "No model program aggregation was found in linked composite resource ID:{}"
                msg = msg.format(linked_res.short_id)
                logger.warning(msg)
                self.stdout.write(self.style.WARNING(msg))

        self.stdout.flush()

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resource_counter = 0
        to_resource_type = 'CompositeResource'

        msg = "THERE ARE CURRENTLY {} MODEL INSTANCE RESOURCES PRIOR TO CONVERSION TO COMPOSITE RESOURCE.".format(
            ModelInstanceResource.objects.count())
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))

        for mi_res in ModelInstanceResource.objects.all().iterator():
            msg = "Migrating model instance resource:{}".format(mi_res.short_id)
            self.stdout.write(self.style.SUCCESS(msg))

            # check resource exists on irods
            istorage = mi_res.get_irods_storage()
            if not istorage.exists(mi_res.root_path):
                err_msg = "Couldn't migrate model instance resource (ID:{}). This resource doesn't exist in iRODS."
                err_msg = err_msg.format(mi_res.short_id)
                logger.error(err_msg)
                self.stdout.write(self.style.ERROR(err_msg))
                self.stdout.flush()
                # skip this mi resource
                continue

            # change the resource_type
            mi_metadata_obj = mi_res.metadata
            mi_res.resource_type = to_resource_type
            mi_res.content_model = to_resource_type.lower()
            mi_res.save()
            # get the converted resource object - CompositeResource
            comp_res = mi_res.get_content_model()

            # set CoreMetaData object for the composite resource
            core_meta_obj = CoreMetaData.objects.create()
            comp_res.content_object = core_meta_obj

            # migrate mi resource core metadata elements to composite resource
            migrate_core_meta_elements(mi_metadata_obj, comp_res)
            comp_res.save()

            # update url attribute of the metadata 'type' element
            type_element = comp_res.metadata.type
            type_element.url = '{0}/terms/{1}'.format(current_site_url(), to_resource_type)
            type_element.save()

            # create a mi aggregation
            try:
                mi_aggr = ModelInstanceLogicalFile.create(resource=comp_res)
                mi_aggr.save()
            except Exception as ex:
                err_msg = 'Failed to create model instance aggregation for resource (ID: {})'
                err_msg = err_msg.format(mi_res.short_id)
                err_msg = err_msg + '\n' + str(ex)
                logger.error(err_msg)
                self.stdout.write(self.style.ERROR(err_msg))
                self.stdout.flush()
                continue

            self.move_files_and_folders_to_aggregation(mi_aggr=mi_aggr, comp_res=comp_res, logger=logger)

            # copy the resource level keywords to aggregation level
            if comp_res.metadata.subjects:
                keywords = [sub.value for sub in comp_res.metadata.subjects.all()]
                mi_aggr.metadata.keywords = keywords
                mi_aggr.metadata.save()
            # copy the model specific metadata to the mi aggregation
            if mi_metadata_obj.model_output:
                mi_aggr.metadata.has_model_output = mi_metadata_obj.model_output.includes_output

            if self._EXECUTED_BY_EXTRA_META_KEY in comp_res.extra_data:
                self.set_executed_by(mi_aggr, comp_res, logger)
            mi_aggr.save()

            # create aggregation level xml files
            mi_aggr.create_aggregation_xml_documents()
            msg = 'One model instance aggregation was created in resource (ID:{})'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))

            comp_res.extra_metadata['MIGRATED_FROM'] = 'Model Instance Resource'
            comp_res.save()
            # set resource to dirty so that resource level xml files (resource map and
            # metadata xml files) will be re-generated as part of next bag download
            try:
                set_dirty_bag_flag(comp_res)
            except Exception as ex:
                err_msg = 'Failed to set bag flag dirty for the converted resource (ID: {})'
                err_msg = err_msg.format(comp_res.short_id)
                err_msg = err_msg + '\n' + str(ex)
                logger.error(err_msg)
                self.stdout.write(self.style.ERROR(err_msg))

            resource_counter += 1
            # delete the instance of model instance metadata that was part of the original model instance resource
            mi_metadata_obj.delete()
            msg = 'Model instance resource (ID: {}) was converted to Composite Resource type'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
            print("_______________________________________________")
            self.stdout.flush()

        if resource_counter > 0:
            msg = "{} MODEL INSTANCE RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE.".format(
                resource_counter)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))

        if ModelInstanceResource.objects.all().count() > 0:
            msg = "NOT ALL MODEL INSTANCE RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE TYPE"
            logger.error(msg)
            self.stdout.write(self.style.WARNING(msg))
            msg = "THERE ARE CURRENTLY {} MODEL INSTANCE RESOURCES AFTER CONVERSION.".format(
                ModelInstanceResource.objects.all().count())
            logger.info(msg)
            self.stdout.write(self.style.WARNING(msg))
        self.stdout.flush()
