import logging
import os

from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag
from hs_core.models import CoreMetaData, ResourceFile
from hs_file_types.models import ModelProgramLogicalFile, ModelProgramResourceFileType
from hs_model_program.models import ModelProgramResource
from ..utils import migrate_core_meta_elements


class Command(BaseCommand):
    help = "Convert all model program resources to composite resource with model program aggregation"

    def create_aggr_folder(self, mp_aggr, comp_res, logger):
        new_folder = "mp"
        ResourceFile.create_folder(comp_res, new_folder)
        mp_aggr.folder = new_folder
        mp_aggr.dataset_name = new_folder
        mp_aggr.save()
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
            self.stdout.write(self.style.SUCCESS(msg))

            # check resource exists on irods
            istorage = mp_res.get_irods_storage()
            if not istorage.exists(mp_res.root_path):
                err_msg = "Model program resource not found in irods (ID: {})".format(mp_res.short_id)
                logger.error(err_msg)
                self.stdout.write(self.style.ERROR(err_msg))
                # skip this mp resource
                continue

            # check resource files exist on irods
            file_missing = False
            for res_file in mp_res.files.all():
                file_path = res_file.public_path
                if not istorage.exists(file_path):
                    err_msg = "File path not found in irods:{}".format(file_path)
                    logger.error(err_msg)
                    err_msg = "Failed to convert model program resource (ID: {}). " \
                              "Resource file is missing on irods".format(mp_res.short_id)
                    self.stdout.write(self.style.ERROR(err_msg))
                    file_missing = True
                    break
            if file_missing:
                # skip this corrupt raster resource for migration
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

            # update url attribute of the metadata 'type' element
            type_element = comp_res.metadata.type
            type_element.url = '{0}/terms/{1}'.format(current_site_url(), to_resource_type)
            type_element.save()
            create_aggregation = True
            if not mp_metadata_obj.program:
                msg = "Resource has no model program specific metadata and no data files. " \
                      "No model program aggregation created for this resource:{}".format(comp_res.short_id)
                if comp_res.files.count() == 0:
                    # original mp resource has no files and no mp specific metadata - no need to create mp aggregation
                    print(msg)
                    create_aggregation = False
                elif comp_res.readme_file is not None and comp_res.files.count() == 1:
                    # original mp resource contains only a readme file and no mp specific metadata - no need to
                    # create mp aggregation
                    print(msg)
                    create_aggregation = False

            if create_aggregation:
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

                if comp_res.files.count() == 0:
                    self.create_aggr_folder(mp_aggr=mp_aggr, comp_res=comp_res, logger=logger)
                elif comp_res.readme_file is not None:
                    if comp_res.files.count() > 2 or comp_res.files.count() == 1:
                        self.create_aggr_folder(mp_aggr=mp_aggr, comp_res=comp_res, logger=logger)
                    # make the all res files part of the aggregation excluding the readme file
                    for res_file in comp_res.files.all():
                        if res_file != comp_res.readme_file:
                            mp_aggr.add_resource_file(res_file)
                            msg = "Added file {} to mp aggregation".format(res_file.file_name)
                            self.stdout.write(self.style.SUCCESS(msg))
                else:
                    if comp_res.files.count() > 1:
                        self.create_aggr_folder(mp_aggr=mp_aggr, comp_res=comp_res, logger=logger)
                    # make the all res files part of the aggregation
                    for res_file in comp_res.files.all():
                        mp_aggr.add_resource_file(res_file)
                        msg = "Added file {} to mp aggregation".format(res_file.file_name)
                        self.stdout.write(self.style.SUCCESS(msg))

                # set the dataset_name field of the aggregation in the case of file based mp aggregation
                if not mp_aggr.folder:
                    aggr_file = mp_aggr.files.first()
                    aggr_filename, _ = os.path.splitext(aggr_file.file_name)
                    mp_aggr.dataset_name = aggr_filename
                    mp_aggr.save()

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
                            self.create_mp_file_type(file_name=file_name, file_type=file_type, mp_aggr=mp_aggr)

                        file_type = ModelProgramResourceFileType.SOFTWARE
                        for file_name in mp_metadata_obj.program.get_software_list():
                            self.create_mp_file_type(file_name=file_name, file_type=file_type, mp_aggr=mp_aggr)

                        file_type = ModelProgramResourceFileType.DOCUMENTATION
                        for file_name in mp_metadata_obj.program.get_documentation_list():
                            self.create_mp_file_type(file_name=file_name, file_type=file_type, mp_aggr=mp_aggr)

                        file_type = ModelProgramResourceFileType.RELEASE_NOTES
                        for file_name in mp_metadata_obj.program.get_releasenotes_list():
                            self.create_mp_file_type(file_name=file_name, file_type=file_type, mp_aggr=mp_aggr)

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
            # delete the instance of model program metadata that was part of the original model instance resource
            mp_metadata_obj.delete()
            msg = 'Model program resource (ID: {}) was converted to Composite Resource type'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
            print("_______________________________________________")

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
