import logging

from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag
from hs_core.models import CoreMetaData
from hs_file_types.models import ModelInstanceLogicalFile
from hs_modelinstance.models import ModelInstanceResource
from ..utils import migrate_core_meta_elements, move_files_and_folders_to_model_aggregation, set_executed_by


class Command(BaseCommand):
    help = "Convert all model instance resources to composite resource with model instance aggregation"
    _EXECUTED_BY_EXTRA_META_KEY = 'EXECUTED_BY_RES_ID'
    _MIGRATION_ISSUE = "MIGRATION ISSUE:"

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resource_counter = 0
        err_resource_counter = 0
        to_resource_type = 'CompositeResource'
        mi_resource_count = ModelInstanceResource.objects.count()
        msg = "THERE ARE CURRENTLY {} MODEL INSTANCE RESOURCES TO MIGRATE TO COMPOSITE RESOURCE.".format(
            mi_resource_count)
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))
        self.stdout.flush()

        for mi_res in ModelInstanceResource.objects.all().iterator():
            msg = "Migrating model instance resource:{}".format(mi_res.short_id)
            self.stdout.write(self.style.SUCCESS(msg))
            self.stdout.flush()

            # check resource exists on irods
            istorage = mi_res.get_irods_storage()
            if not istorage.exists(mi_res.root_path):
                err_resource_counter += 1
                err_msg = "{}Couldn't migrate model instance resource (ID:{}). This resource doesn't exist in iRODS."
                err_msg = err_msg.format(self._MIGRATION_ISSUE, mi_res.short_id)
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
            mi_aggr = ModelInstanceLogicalFile.create(resource=comp_res)
            mi_aggr.save()
            try:
                move_files_and_folders_to_model_aggregation(command=self, model_aggr=mi_aggr, comp_res=comp_res,
                                                            logger=logger, aggr_name='model-instance')
            except Exception as ex:
                err_resource_counter += 1
                err_msg = '{}Failed to move files/folders into model instance aggregation for resource (ID: {})'
                err_msg = err_msg.format(self._MIGRATION_ISSUE, comp_res.short_id)
                err_msg = err_msg + '\n' + str(ex)
                logger.error(err_msg)
                self.stdout.write(self.style.ERROR(err_msg))
                self.stdout.flush()
                mi_metadata_obj.delete()
                continue

            # copy the resource level keywords to aggregation level
            if comp_res.metadata.subjects:
                keywords = [sub.value for sub in comp_res.metadata.subjects.all()]
                mi_aggr.metadata.keywords = keywords
                mi_aggr.metadata.save()
            # copy the model specific metadata to the mi aggregation
            if mi_metadata_obj.model_output:
                mi_aggr.metadata.has_model_output = mi_metadata_obj.model_output.includes_output

            if self._EXECUTED_BY_EXTRA_META_KEY in comp_res.extra_data:
                if not set_executed_by(self, mi_aggr, comp_res, logger):
                    err_resource_counter += 1
            mi_aggr.save()

            # set aggregation metadata to dirty so that aggregation meta xml files are generated as part of aggregation
            # or resource bag download
            mi_aggr.set_metadata_dirty()
            msg = 'One model instance aggregation was created in resource (ID:{})'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))

            comp_res.extra_metadata['MIGRATED_FROM'] = 'Model Instance Resource'
            comp_res.save()
            set_dirty_bag_flag(comp_res)
            resource_counter += 1
            # delete the instance of model instance metadata that was part of the original model instance resource
            mi_metadata_obj.delete()
            msg = 'Model instance resource (ID: {}) was migrated to Composite Resource'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
            print("_______________________________________________")
            self.stdout.flush()

        print("________________MIGRATION SUMMARY_________________")
        msg = "{} MODEL INSTANCE RESOURCES EXISTED PRIOR TO MIGRATION TO COMPOSITE RESOURCE".format(
            mi_resource_count)
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))

        msg = "{} MODEL INSTANCE RESOURCES HAD ISSUES DURING MIGRATION TO COMPOSITE RESOURCE".format(
            err_resource_counter)
        if err_resource_counter > 0:
            logger.error(msg)
            self.stdout.write(self.style.ERROR(msg))
        else:
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))

        msg = "{} MODEL INSTANCE RESOURCES WERE MIGRATED TO COMPOSITE RESOURCE".format(
            resource_counter)
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))

        mi_resource_count = ModelInstanceResource.objects.count()
        if mi_resource_count > 0:
            msg = "NOT ALL MODEL INSTANCE RESOURCES WERE MIGRATED TO COMPOSITE RESOURCE"
            logger.error(msg)
            self.stdout.write(self.style.WARNING(msg))
            msg = "THERE ARE CURRENTLY {} MODEL INSTANCE RESOURCES AFTER MIGRATION.".format(
                mi_resource_count)
            logger.info(msg)
            self.stdout.write(self.style.WARNING(msg))
        else:
            msg = "ALL MODEL INSTANCE RESOURCES WERE MIGRATED TO COMPOSITE RESOURCE"
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
        self.stdout.flush()
