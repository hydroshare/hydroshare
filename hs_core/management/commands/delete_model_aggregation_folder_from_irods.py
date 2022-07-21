import os

from django.conf import settings
from django.core.management.base import BaseCommand

from hs_model_program.models import ModelProgramResource
from hs_modelinstance.models import ModelInstanceResource
from hs_modflow_modelinstance.models import MODFLOWModelInstanceResource
from hs_swat_modelinstance.models import SWATModelInstanceResource


class Command(BaseCommand):
    """This command needs to be run to cleanup model aggregation folder from iRODS when testing model migration commands
    NOTE: This command MUST not be used in production. After running this command, do a data update so that the model
    resources are same as in the production.
    """

    help = "Deletes model aggregation folders which were created as part of model resource migration."

    def delete_model_aggregation_folders(self, model_res):
        # deletes folders potentially created by model resource migration command
        istorage = model_res.get_irods_storage()
        model_res_type_folder_mapping = {"ModelProgramResource": "model-program",
                                         "ModelInstanceResource": "model-instance",
                                         "MODFLOWModelInstanceResource": "modflow-model-instance",
                                         "SWATModelInstanceResource": "swat-model-instance"}
        if not istorage.exists(model_res.root_path):
            err_msg = f">> Resource (ID:{model_res.short_id}) was not found in iRODS"
            print(err_msg, flush=True)
            return

        base_folder_name = model_res_type_folder_mapping[model_res.resource_type]
        folder_name = base_folder_name
        folder_count = 0
        while True:
            full_folder_path_to_delete = os.path.join(model_res.root_path, 'data', 'contents', folder_name)
            if not istorage.exists(full_folder_path_to_delete):
                err_msg = f">> Folder ({full_folder_path_to_delete}) was not found in iRODS"
                print(err_msg, flush=True)
                # no need to further look for folders
                return

            istorage.delete(full_folder_path_to_delete)
            msg = "Deleted folder:{}".format(full_folder_path_to_delete)
            print(msg, flush=True)
            # next folder to delete
            folder_count += 1
            folder_name = f"{base_folder_name}-{folder_count}"

    def handle(self, *args, **options):
        if not settings.DEBUG:
            err_msg = "This command can only be run in DEBUG mode"
            print(err_msg, flush=True)
            return

        LINE_LENGTH = 50
        res_count = 0
        model_res_classes = [ModelProgramResource, ModelInstanceResource, SWATModelInstanceResource,
                             MODFLOWModelInstanceResource]
        for model_res_class in model_res_classes:
            msg = f"Deleting Folders for {model_res_class.__name__} Resources"
            print(msg)
            print("=" * LINE_LENGTH, flush=True)
            type_res_count = model_res_class.objects.count()
            for model_res in model_res_class.objects.all().iterator():
                msg = f"Deleting folder(s) for resource:{model_res.short_id}"
                print(msg, flush=True)
                self.delete_model_aggregation_folders(model_res)
                print("_" * LINE_LENGTH, flush=True)

            res_count += type_res_count
            msg = f"{type_res_count} {model_res_class.__name__} Resources were processed"
            print(msg)
            print("_" * LINE_LENGTH, flush=True)

        msg = f"{res_count} Model Type Resources were processed"
        print(msg)
        print("_" * LINE_LENGTH)
