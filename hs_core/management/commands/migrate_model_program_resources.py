import logging
import os

from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag
from hs_core.models import CoreMetaData, ResourceFile
from hs_file_types.models import ModelProgramLogicalFile, ModelProgramResourceFileType
from hs_model_program.models import ModelProgramResource
from ..utils import migrate_core_meta_elements


class Command(BaseCommand):
    help = "Convert all model program resources to composite resource with one model program aggregation"

    def get_aggregation_folder_name(self, comp_res):
        # generate a folder name if the default name already exists
        default_folder_name = "model-program"
        folder_name = default_folder_name
        istorage = comp_res.get_irods_storage()
        folder_path = os.path.join(comp_res.file_path, default_folder_name)
        post_fix = 1
        while istorage.exists(folder_path):
            folder_name = "{}-{}".format(default_folder_name, post_fix)
            folder_path = os.path.join(comp_res.file_path, folder_name)
            post_fix += 1
        return folder_name

    def move_files_and_folders_to_aggregation(self, mp_aggr, comp_res, logger):
        # create a new folder for mp aggregation to which all files and folders will be moved
        new_folder = self.get_aggregation_folder_name(comp_res)
        ResourceFile.create_folder(comp_res, new_folder, migrating_resource=True)
        mp_aggr.folder = new_folder
        mp_aggr.dataset_name = new_folder
        mp_aggr.save()
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

                        # Note: some of the files returned by list_folder() may not exist in iRODS
                        res_file_objs = ResourceFile.list_folder(comp_res, folder_to_move)
                        tgt_short_path = os.path.join(new_folder, folder_to_move)
                        for fobj in res_file_objs:
                            src_path = fobj.storage_path
                            new_path = src_path.replace(folder_to_move, tgt_short_path, 1)
                            if istorage.exists(new_path):
                                fobj.set_storage_path(new_path)
                                mp_aggr.add_resource_file(fobj)
                                msg = "Added file ({}) to model program aggregation".format(fobj.short_path)
                                logger.info(msg)
                                self.stdout.write(self.style.SUCCESS(msg))
                            else:
                                err_msg = "File ({}) is missing in iRODS. File not added to the aggregation"
                                err_msg = err_msg.format(new_path)
                                logger.warn(err_msg)
                                self.stdout.write(self.style.WARNING(err_msg))
                    else:
                        msg = "Moved file ({}) to the new aggregation folder:{}".format(src_short_path, new_folder)
                        logger.info(msg)
                        self.stdout.write(self.style.SUCCESS(msg))
                        res_file.set_storage_path(tgt_full_path)
                        mp_aggr.add_resource_file(res_file)
                        msg = "Added file ({}) to model program aggregation".format(res_file.short_path)
                        logger.info(msg)
                        self.stdout.write(self.style.SUCCESS(msg))
                else:
                    err_msg = "File path ({}) not found in iRODS. Couldn't make this file part of " \
                              "the model program aggregation.".format(src_full_path)
                    logger.warn(err_msg)
                    self.stdout.write(self.style.WARNING(err_msg))
                self.stdout.flush()

    def create_mp_file_type(self, file_name, file_type, mp_aggr):
        for aggr_file in mp_aggr.files.all():
            if aggr_file.file_name == file_name:
                if not ModelProgramResourceFileType.objects.filter(
                        file_type=file_type,
                        res_file=aggr_file,
                        mp_metadata=mp_aggr.metadata
                ).exists():
                    ModelProgramResourceFileType.objects.create(file_type=file_type,
                                                                res_file=aggr_file,
                                                                mp_metadata=mp_aggr.metadata)
                break

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resource_counter = 0
        to_resource_type = 'CompositeResource'
        mp_resource_count = ModelProgramResource.objects.count()
        msg = "THERE ARE CURRENTLY {} MODEL PROGRAM RESOURCES PRIOR TO CONVERSION TO COMPOSITE RESOURCE.".format(
            mp_resource_count)
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))
        if mp_resource_count == 0:
            msg = "THERE ARE NO MODEL PROGRAM RESOURCES TO MIGRATE."
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
            return

        for mp_res in ModelProgramResource.objects.all().iterator():
            msg = "Migrating model program resource:{}".format(mp_res.short_id)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))

            # check resource exists on irods
            istorage = mp_res.get_irods_storage()
            if not istorage.exists(mp_res.root_path):
                err_msg = "Couldn't migrate model program resource (ID:{}). This resource doesn't exist in iRODS."
                err_msg = err_msg.format(mp_res.short_id)
                logger.error(err_msg)
                self.stdout.write(self.style.ERROR(err_msg))
                # skip this mp resource
                continue

            # change the resource_type
            mp_metadata_obj = mp_res.metadata
            mp_res.resource_type = to_resource_type
            mp_res.content_model = to_resource_type.lower()
            mp_res.save()
            # get the converted resource object - CompositeResource
            comp_res = mp_res.get_content_model()

            # set CoreMetaData object for the composite resource
            core_meta_obj = CoreMetaData.objects.create()
            comp_res.content_object = core_meta_obj

            # migrate mp resource core metadata elements to composite resource
            migrate_core_meta_elements(mp_metadata_obj, comp_res)
            comp_res.save()

            # update url attribute of the metadata 'type' element
            type_element = comp_res.metadata.type
            type_element.url = '{0}/terms/{1}'.format(current_site_url(), to_resource_type)
            type_element.save()

            # create a mp aggregation
            try:
                mp_aggr = ModelProgramLogicalFile.create(resource=comp_res)
                mp_aggr.save()
            except Exception as ex:
                err_msg = 'Failed to create model program aggregation for resource (ID: {})'
                err_msg = err_msg.format(mp_res.short_id)
                err_msg = err_msg + '\n' + str(ex)
                logger.error(err_msg)
                self.stdout.write(self.style.ERROR(err_msg))
                continue

            self.move_files_and_folders_to_aggregation(mp_aggr=mp_aggr, comp_res=comp_res, logger=logger)

            # copy the resource level keywords to aggregation level
            if comp_res.metadata.subjects:
                keywords = [sub.value for sub in comp_res.metadata.subjects.all()]
                mp_aggr.metadata.keywords = keywords
                mp_aggr.metadata.save()

            if mp_metadata_obj.program:
                if mp_aggr.files.count() > 0:
                    # create mp program file types
                    file_type = ModelProgramResourceFileType.ENGINE
                    for file_name in mp_metadata_obj.program.get_engine_list():
                        if file_name:
                            self.create_mp_file_type(file_name=file_name, file_type=file_type, mp_aggr=mp_aggr)
                            msg = "Setting file:{} as computational engine".format(file_name)
                            logger.info(msg)
                            self.stdout.write(self.style.SUCCESS(msg))

                    file_type = ModelProgramResourceFileType.SOFTWARE
                    for file_name in mp_metadata_obj.program.get_software_list():
                        if file_name:
                            self.create_mp_file_type(file_name=file_name, file_type=file_type, mp_aggr=mp_aggr)
                            msg = "Setting file:{} as software".format(file_name)
                            logger.info(msg)
                            self.stdout.write(self.style.SUCCESS(msg))

                    file_type = ModelProgramResourceFileType.DOCUMENTATION
                    for file_name in mp_metadata_obj.program.get_documentation_list():
                        if file_name:
                            self.create_mp_file_type(file_name=file_name, file_type=file_type, mp_aggr=mp_aggr)
                            msg = "Setting file:{} as documentation".format(file_name)
                            logger.info(msg)
                            self.stdout.write(self.style.SUCCESS(msg))

                    file_type = ModelProgramResourceFileType.RELEASE_NOTES
                    for file_name in mp_metadata_obj.program.get_releasenotes_list():
                        if file_name:
                            self.create_mp_file_type(file_name=file_name, file_type=file_type, mp_aggr=mp_aggr)
                            msg = "Setting file:{} as release notes".format(file_name)
                            logger.info(msg)
                            self.stdout.write(self.style.SUCCESS(msg))

                    self.stdout.flush()

                if mp_metadata_obj.program.modelReleaseDate:
                    mp_aggr.metadata.release_date = mp_metadata_obj.program.modelReleaseDate
                if mp_metadata_obj.program.modelVersion:
                    mp_aggr.metadata.version = mp_metadata_obj.program.modelVersion
                if mp_metadata_obj.program.modelWebsite:
                    mp_aggr.metadata.website = mp_metadata_obj.program.modelWebsite
                if mp_metadata_obj.program.modelCodeRepository:
                    mp_aggr.metadata.code_repository = mp_metadata_obj.program.modelCodeRepository
                if mp_metadata_obj.program.modelProgramLanguage:
                    languages = mp_metadata_obj.program.modelProgramLanguage.split(',')
                    languages = [lang.strip() for lang in languages]
                    mp_aggr.metadata.programming_languages = languages
                if mp_metadata_obj.program.modelOperatingSystem:
                    op_systems = mp_metadata_obj.program.modelOperatingSystem.split(',')
                    op_systems = [op.strip() for op in op_systems]
                    mp_aggr.metadata.operating_systems = op_systems

                mp_aggr.save()

            # create aggregation level xml files
            mp_aggr.create_aggregation_xml_documents()
            msg = 'One model program aggregation was created in resource (ID:{})'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))

            comp_res.extra_metadata['MIGRATED_FROM'] = 'Model Program Resource'
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
            # delete the instance of model program metadata that was part of the original model instance resource
            mp_metadata_obj.delete()
            msg = 'Model program resource (ID: {}) was converted to Composite Resource type'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
            print("_______________________________________________")
            self.stdout.flush()

        if resource_counter > 0:
            msg = "{} MODEL PROGRAM RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE.".format(
                resource_counter)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))

        if mp_resource_count > resource_counter:
            msg = "{} MODEL PROGRAM RESOURCE(S) WAS/WERE NOT CONVERTED TO COMPOSITE RESOURCE TYPE"
            msg = msg.format(mp_resource_count - resource_counter)
            logger.error(msg)
            self.stdout.write(self.style.WARNING(msg))
        elif mp_resource_count > 0:
            msg = "ALL MODEL PROGRAM RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE TYPE"
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
        self.stdout.flush()
