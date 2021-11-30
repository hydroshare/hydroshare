import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from hs_model_program.models import ModelProgramResource
from hs_modelinstance.models import ModelInstanceResource
from hs_modflow_modelinstance.models import MODFLOWModelInstanceResource
from hs_swat_modelinstance.models import SWATModelInstanceResource


class Command(BaseCommand):
    """This command needs to be run to cleanup model aggregation folder from iRODS when testing model migration commands
    NOTE: This command MUST not be used in production
    """

    help = "Save the id of the linked model program resource in model instance resource as part of preparing model" \
           "instance resource migration to composite resource"

    def add_arguments(self, parser):

        parser.add_argument('type', type=str,   help='limit to resources of a particular model resource type')
        # a list of resource id's for which aggregation folder needs to be deleted.
        parser.add_argument('resource_ids', nargs='*', type=str)

    def process_resource(self, model_res, resource_type, logger):
        istorage = model_res.get_irods_storage()
        if not istorage.exists(model_res.root_path):
            err_msg = ">> Resource (ID:{}) doesn't exist in iRODS"
            self.stdout.write(self.style.ERROR(err_msg))
            return
        if resource_type == "ModelProgram":
            folder_name = 'model-program'
            full_folder_path_to_delete = os.path.join(model_res.file_path, folder_name)
        else:
            folder_name = 'model-instance'
            full_folder_path_to_delete = os.path.join(model_res.file_path, folder_name)

        aggr_meta_file = "{}_meta.xml".format(folder_name)

        if not istorage.exists(full_folder_path_to_delete):
            err_msg = ">> Folder ({}) was not found in iRODS".format(full_folder_path_to_delete)
            self.stdout.write(self.style.ERROR(err_msg))
            return
        full_aggr_meta_file_path = os.path.join(full_folder_path_to_delete, aggr_meta_file)
        if not istorage.exists(full_aggr_meta_file_path):
            # check for empty folder
            directory_in_irods = model_res.get_irods_path(full_folder_path_to_delete)

            store = istorage.listdir(directory_in_irods)
            # store[1] is a list of files in the directory
            if len(store[1]) > 0:
                err_msg = ">> No aggregation meta file exist in iRODS and the folder is not empty:{}. " \
                          "Not deleting folder."
                err_msg = err_msg.format(full_folder_path_to_delete)
                self.stdout.write(self.style.ERROR(err_msg))
                return

        # delete the folder
        istorage.delete(full_folder_path_to_delete)
        msg = "Deleted folder:{}".format(full_folder_path_to_delete)
        self.stdout.write(self.style.SUCCESS(msg))
        logger.info(msg)

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        if not settings.DEBUG:
            err_msg = "This command can only be run in DEBUG mode"
            self.stdout.write(self.style.ERROR(err_msg))
            self.stdout.flush()
            return

        model_class_map = {'ModelProgram': ModelProgramResource, 'ModelInstance': ModelInstanceResource,
                           'SWATModelInstance': SWATModelInstanceResource,
                           'MODFLOWModelInstance': MODFLOWModelInstanceResource}
        resource_type = options['type']
        if resource_type not in model_class_map.keys():
            allowed_types = ", ".join(model_class_map.keys())
            err_msg = "Invalid resource type:{}, Allowed resource types are: {}".format(options['type'], allowed_types)
            self.stdout.write(self.style.ERROR(err_msg))
            self.stdout.flush()
            return

        model_class = model_class_map[resource_type]
        if len(options['resource_ids']) > 0:
            for rid in options['resource_ids']:
                msg = "Processing resource:{}".format(rid)
                self.stdout.write(self.style.SUCCESS(msg))
                self.stdout.flush()
                try:
                    model_res = model_class.objects.get(short_id=rid)
                except model_class.DoesNotExist:
                    err_msg = "No {} resource was found for resource id:{}".format(resource_type, rid)
                    self.stdout.write(self.style.ERROR(err_msg))
                    continue

                self.process_resource(model_res, resource_type, logger)

            msg = "\n{} {} RESOURCES WERE PROCESSED".format(len(options['resource_ids']), resource_type)
            self.stdout.write(self.style.SUCCESS(msg))
            logger.info(msg)
            self.stdout.flush()
        else:
            counter = 0
            for model_res in model_class.objects.all().iterator():
                counter += 1
                msg = "Processing resource:{}".format(model_res.short_id)
                self.stdout.write(self.style.SUCCESS(msg))
                self.stdout.flush()
                self.process_resource(model_res, resource_type, logger)

            msg = "\n{} {} RESOURCES WERE PROCESSED".format(counter, resource_type)
            self.stdout.write(self.style.SUCCESS(msg))
            logger.info(msg)
            self.stdout.flush()
