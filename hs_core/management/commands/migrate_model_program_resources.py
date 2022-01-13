import logging
import os

from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag
from hs_core.models import CoreMetaData
from hs_file_types.models import ModelProgramLogicalFile, ModelProgramResourceFileType
from hs_model_program.models import ModelProgramResource
from ..utils import migrate_core_meta_elements, move_files_and_folders_to_model_aggregation


class Command(BaseCommand):
    help = "Convert all model program resources to composite resource with one model program aggregation"

    def create_mp_file_type(self, orig_mp_file_path, file_type, mp_aggr, file_type_name, logger):
        # Note: The *orig_mp_file_path* in the original mp resource can be just a file name (test.txt), or
        # a short path (folder-1/test.txt) or path starting with resource file path([res_id]/data/contents/test.txt)
        # The *orig_mp_file_path* not always includes the folder path in which the file exist. If the
        # original mp resource has duplicate filenames (without folder path) for multiple mp file types
        # (e.g. test.txt as 'documentation' as well as text.txt as 'release notes', then the same file will be
        # set to multiple mp file types as part of the migration.
        msg = "Setting file (original file path):{} as {}".format(orig_mp_file_path, file_type_name)
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))

        comp_res = mp_aggr.resource
        for aggr_file in mp_aggr.files.all():
            file_folder = ''
            if orig_mp_file_path.startswith(comp_res.file_path):
                orig_mp_file_path = orig_mp_file_path[len(comp_res.file_path) + 1:]

            if '/' in orig_mp_file_path:
                file_folder, file_name = os.path.split(orig_mp_file_path)
            else:
                file_name = orig_mp_file_path

            if file_folder:
                if not aggr_file.file_folder == "{}/{}".format(mp_aggr.folder, file_folder):
                    continue

            if aggr_file.file_name == file_name:
                if not ModelProgramResourceFileType.objects.filter(
                        file_type=file_type,
                        res_file=aggr_file,
                        mp_metadata=mp_aggr.metadata
                ).exists():
                    ModelProgramResourceFileType.objects.create(file_type=file_type,
                                                                res_file=aggr_file,
                                                                mp_metadata=mp_aggr.metadata)

                    msg = "File (new file path):{} was set as {}".format(aggr_file.short_path, file_type_name)
                    logger.info(msg)
                    self.stdout.write(self.style.SUCCESS(msg))

                break

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resource_counter = 0
        to_resource_type = 'CompositeResource'
        mp_resource_count = ModelProgramResource.objects.count()
        msg = "THERE ARE CURRENTLY {} MODEL PROGRAM RESOURCES TO MIGRATE TO COMPOSITE RESOURCE.".format(
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

            move_files_and_folders_to_model_aggregation(command=self, model_aggr=mp_aggr, comp_res=comp_res,
                                                        logger=logger, aggr_name='model-program')

            # copy the resource level keywords to aggregation level
            if comp_res.metadata.subjects:
                keywords = [sub.value for sub in comp_res.metadata.subjects.all()]
                mp_aggr.metadata.keywords = keywords
                mp_aggr.metadata.save()

            if mp_metadata_obj.program:
                if mp_aggr.files.count() > 0:
                    # create mp program file types
                    file_type = ModelProgramResourceFileType.ENGINE
                    for mp_file_path in mp_metadata_obj.program.get_engine_list():
                        if mp_file_path:
                            self.create_mp_file_type(orig_mp_file_path=mp_file_path, file_type=file_type,
                                                     mp_aggr=mp_aggr,
                                                     file_type_name='computational engine', logger=logger)

                    file_type = ModelProgramResourceFileType.SOFTWARE
                    for file_name in mp_metadata_obj.program.get_software_list():
                        if file_name:
                            self.create_mp_file_type(orig_mp_file_path=file_name, file_type=file_type, mp_aggr=mp_aggr,
                                                     file_type_name='software', logger=logger)

                    file_type = ModelProgramResourceFileType.DOCUMENTATION
                    for file_name in mp_metadata_obj.program.get_documentation_list():
                        if file_name:
                            self.create_mp_file_type(orig_mp_file_path=file_name, file_type=file_type, mp_aggr=mp_aggr,
                                                     file_type_name='documentation', logger=logger)

                    file_type = ModelProgramResourceFileType.RELEASE_NOTES
                    for file_name in mp_metadata_obj.program.get_releasenotes_list():
                        if file_name:
                            self.create_mp_file_type(orig_mp_file_path=file_name, file_type=file_type, mp_aggr=mp_aggr,
                                                     file_type_name='release notes', logger=logger)
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

            # set aggregation metadata to dirty so that aggregation meta xml files are generated as part of aggregation
            # or resource bag download
            mp_aggr.set_metadata_dirty()
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

        if ModelProgramResource.objects.all().count() > 0:
            msg = "NOT ALL MODEL PROGRAM RESOURCES WERE MIGRATED TO COMPOSITE RESOURCE"
            logger.error(msg)
            self.stdout.write(self.style.WARNING(msg))
            msg = "THERE ARE CURRENTLY {} MODEL PROGRAM RESOURCES AFTER MIGRATION.".format(
                ModelProgramResource.objects.all().count())
            logger.info(msg)
            self.stdout.write(self.style.WARNING(msg))
        else:
            msg = "ALL MODEL PROGRAM RESOURCES WERE MIGRATED TO COMPOSITE RESOURCE"
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
        self.stdout.flush()
