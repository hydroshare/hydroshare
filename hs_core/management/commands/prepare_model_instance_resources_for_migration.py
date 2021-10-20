import logging

from django.core.management.base import BaseCommand

from hs_modelinstance.models import ModelInstanceResource


class Command(BaseCommand):
    help = "Save the id of the linked model program resource in model instance resource as part of preparing model" \
           "instance resource migration to composite resource"

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resource_counter_executed_by = 0
        resource_counter_modified = 0

        msg = "THERE ARE CURRENTLY {} MODEL INSTANCE RESOURCES FOR MIGRATION PREPARATION.".format(
            ModelInstanceResource.objects.count())
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))

        for mi_res in ModelInstanceResource.objects.all().iterator():
            msg = "Preparing model instance resource for migration:{}".format(mi_res.short_id)
            self.stdout.write(self.style.SUCCESS(msg))

            # check resource exists on irods
            istorage = mi_res.get_irods_storage()
            if not istorage.exists(mi_res.root_path):
                err_msg = "Model instance resource not found in irods (ID: {})".format(mi_res.short_id)
                logger.error(err_msg)
                self.stdout.write(self.style.ERROR(err_msg))
                # skip this mi resource
                continue
            if mi_res.metadata.executed_by:
                resource_counter_executed_by += 1
                linked_mp_res = mi_res.metadata.executed_by.model_program_fk
                istorage = linked_mp_res.get_irods_storage()
                if not istorage.exists(linked_mp_res.root_path):
                    err_msg = "Linked Model program resource was not found in irods (ID: {})".format(linked_mp_res.short_id)
                    logger.error(err_msg)
                    self.stdout.write(self.style.ERROR(err_msg))
                else:
                    # extra_meta = mi_res.extra_metadata
                    # extra_meta['MIGRATED_PROGRAM_RES_ID'] = linked_mp_res.short_id
                    mi_res.extra_metadata['MIGRATED_PROGRAM_RES_ID'] = linked_mp_res.short_id
                    mi_res.save()
                    resource_counter_modified += 1
                    msg = "Saved the ID:{} of the linked model program resource in model instance resource"
                    msg = msg.format(linked_mp_res.short_id)
                    logger.info(msg)
                    self.stdout.write(self.style.SUCCESS(msg))
            else:
                msg = "This model instance resource ({}) is not linked to a model program resource"
                msg = msg.format(mi_res.short_id)
                logger.info(msg)
                self.stdout.write(self.style.SUCCESS(msg))
            print("_______________________________________________")

        if resource_counter_executed_by == resource_counter_modified:
            msg = "ALL MODEL INSTANCE RESOURCES WITH LINKED MODEL PROGRAM RESOURCE WERE SUCCESSFULLY " \
                  "PREPARED FOR MIGRATION"
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
        else:
            msg = "{} MODEL INSTANCE RESOURCES WITH LINKED MODEL PROGRAM RESOURCE WERE NOT SUCCESSFULLY " \
                  "PREPARED FOR MIGRATION".format(resource_counter_executed_by - resource_counter_modified)
            logger.warning(msg)
            self.stdout.write(self.style.WARNING(msg))
