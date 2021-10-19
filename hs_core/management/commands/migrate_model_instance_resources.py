import logging
import os

from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag
from hs_core.models import CoreMetaData, ResourceFile
from hs_file_types.models import ModelInstanceLogicalFile
from hs_modelinstance.models import ModelInstanceResource
from ..utils import migrate_core_meta_elements


class Command(BaseCommand):
    help = "Convert all model instance resources to composite resource with model instance aggregation"

    def create_aggr_folder(self, mi_aggr, comp_res, logger):
        new_folder = "mi"
        ResourceFile.create_folder(comp_res, new_folder)
        mi_aggr.folder = new_folder
        mi_aggr.dataset_name = new_folder
        mi_aggr.save()
        msg = "Added a new folder '{}' to the resource:{}".format(new_folder, comp_res.short_id)
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))
        # move files to the new folder
        istorage = comp_res.get_irods_storage()

        for res_file in comp_res.files.all():
            if res_file != comp_res.readme_file:
                src_full_path = os.path.join(comp_res.file_path, res_file.file_name)
                tgt_full_path = os.path.join(comp_res.file_path, new_folder, res_file.file_name)
                istorage.moveFile(src_full_path, tgt_full_path)
                res_file.set_storage_path(tgt_full_path)
                msg = "Moved file:{} to the new folder:{}".format(res_file.file_name, new_folder)
                self.stdout.write(self.style.SUCCESS(msg))

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
                err_msg = "Model instance resource not found in irods (ID: {})".format(mi_res.short_id)
                logger.error(err_msg)
                self.stdout.write(self.style.ERROR(err_msg))
                # skip this mi resource
                continue

            # check resource files exist on irods
            file_missing = False
            for res_file in mi_res.files.all().iterator():
                file_path = res_file.public_path
                if not istorage.exists(file_path):
                    err_msg = "File path not found in irods:{}".format(file_path)
                    logger.error(err_msg)
                    err_msg = "Failed to convert model instance resource (ID: {}). " \
                              "Resource file is missing on irods".format(mi_res.short_id)
                    self.stdout.write(self.style.ERROR(err_msg))
                    file_missing = True
                    break
            if file_missing:
                # skip this corrupt raster resource for migration
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

            # update url attribute of the metadata 'type' element
            type_element = comp_res.metadata.type
            type_element.url = '{0}/terms/{1}'.format(current_site_url(), to_resource_type)
            type_element.save()
            create_aggregation = True
            if not mi_metadata_obj.model_output and not mi_metadata_obj.executed_by:
                msg = "Resource has no model instance specific metadata and no data files. " \
                      "No model instance aggregation created for this resource:{}".format(comp_res.short_id)
                if comp_res.files.count() == 0:
                    # original mi resource has no files and no mi specific metadata - no need to create mi aggregation
                    print(msg)
                    create_aggregation = False
                elif comp_res.readme_file is not None and comp_res.files.count() == 1:
                    # original mi resource contains only a readme file and no mi specific metadata - no need to
                    # create mi aggregation
                    print(msg)
                    create_aggregation = False

            if create_aggregation:
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
                    continue

                if comp_res.files.count() == 0:
                    self.create_aggr_folder(mi_aggr=mi_aggr, comp_res=comp_res, logger=logger)
                elif comp_res.readme_file is not None:
                    if comp_res.files.count() > 2 or comp_res.files.count() == 1:
                        self.create_aggr_folder(mi_aggr=mi_aggr, comp_res=comp_res, logger=logger)
                    # make the all res files part of the aggregation excluding the readme file
                    for res_file in comp_res.files.all():
                        if res_file != comp_res.readme_file:
                            mi_aggr.add_resource_file(res_file)
                            msg = "Added file {} to mi aggregation".format(res_file.file_name)
                            self.stdout.write(self.style.SUCCESS(msg))
                else:
                    if comp_res.files.count() > 1:
                        self.create_aggr_folder(mi_aggr=mi_aggr, comp_res=comp_res, logger=logger)
                    # make the all res files part of the aggregation
                    for res_file in comp_res.files.all():
                        mi_aggr.add_resource_file(res_file)
                        msg = "Added file {} to mi aggregation".format(res_file.file_name)
                        self.stdout.write(self.style.SUCCESS(msg))

                # set the dataset_name field of the aggregation in the case of file based mi aggregation
                if not mi_aggr.folder:
                    aggr_file = mi_aggr.files.first()
                    aggr_filename, _ = os.path.splitext(aggr_file.file_name)
                    mi_aggr.dataset_name = aggr_filename
                    mi_aggr.save()

                # copy the resource level keywords to aggregation level
                if comp_res.metadata.subjects:
                    keywords = [sub.value for sub in comp_res.metadata.subjects.all()]
                    mi_aggr.metadata.keywords = keywords
                    mi_aggr.metadata.save()
                # copy the model specific metadata to the mi aggregation
                if mi_metadata_obj.model_output:
                    mi_aggr.metadata.has_model_output = mi_metadata_obj.model_output.includes_output
                if mi_metadata_obj.executed_by:
                    # need to copy the mi aggregation from the linked composite resource to over to this resource
                    linked_res = comp_res.metadata.executed_by.model_program_fk
                    # TODO: need to copy the mp aggregation from the linked_res
                    pass

                mi_aggr.save()

                # create aggregation level xml files
                mi_aggr.create_aggregation_xml_documents()
                msg = 'One model instance aggregation was created in resource (ID:{})'
                msg = msg.format(comp_res.short_id)
                logger.info(msg)
                self.stdout.write(self.style.SUCCESS(msg))

            # set resource to dirty so that resource level xml files (resource map and
            # metadata xml files) will be re-generated as part of next bag download
            comp_res.save()
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
