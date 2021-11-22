import json
import logging
import os

import jsonschema
from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag, get_resource_by_shortkey
from hs_core.models import CoreMetaData, ResourceFile
from hs_file_types.models import ModelInstanceLogicalFile
from hs_modflow_modelinstance.models import MODFLOWModelInstanceResource
from hs_modflow_modelinstance.serializers import MODFLOWModelInstanceMetaDataSerializerMigration
from ..utils import migrate_core_meta_elements, get_modflow_meta_schema


class Command(BaseCommand):
    help = "Convert all MODFLOW model instance resources to composite resource with model instance aggregation"
    _EXECUTED_BY_EXTRA_META_KEY = 'EXECUTED_BY_RES_ID'

    def generate_metadata_json(self, modflow_meta):
        """
        Generate modflow metadata in JSON format from the metadata of the modflow model instance metadata
        :param modflow_meta: This is the original metadata object from the modflow model instance resource
        """
        serializer = MODFLOWModelInstanceMetaDataSerializerMigration(modflow_meta)
        data = serializer.data
        # mapping of json based field names to modflow meta database field names
        key_maps = {'studyArea': 'study_area', 'modelCalibration': 'model_calibration',
                    'groundwaterFlow': 'ground_water_flow', 'gridDimensions': 'grid_dimensions',
                    'stressPeriod': 'stress_period', 'modelInputs': 'model_inputs'}

        for key, value in key_maps.items():
            data[key] = data.pop(value, None)
            if data[key] is None or not data[key]:
                data.pop(key)

        general_elements = data.pop('general_elements', None)
        if general_elements is not None:
            data['modelSolver'] = general_elements['modelSolver']
            data['modelParameter'] = general_elements['modelParameter']
            data['subsidencePackage'] = general_elements['subsidencePackage']

        if 'stressPeriod' in data:
            for key in list(data['stressPeriod']):
                new_key = ""
                if key == 'stressPeriodType':
                    v = data['stressPeriod'].pop(key)
                    new_key = 'type'
                elif key == 'steadyStateValue':
                    v = data['stressPeriod'].pop(key)
                    new_key = 'lengthOfSteadyStateStressPeriod'
                elif key == 'transientStateValueType':
                    v = data['stressPeriod'].pop(key)
                    new_key = 'typeOfTransientStateStressPeriod'
                elif key == 'transientStateValue':
                    v = data['stressPeriod'].pop(key)
                    new_key = 'lengthOfTransientStateStressPeriod'
                if new_key:
                    data['stressPeriod'][new_key] = v

        if general_elements is not None:
            output_control_pkg = general_elements['output_control_package']
            if output_control_pkg:
                data['outputControlPackage'] = {'OC': False, 'HYD': False, 'GAGE': False, 'LMT6': False, 'MNWI': False}
                for key in data['outputControlPackage']:
                    for pkg in output_control_pkg:
                        if pkg['description'] == key:
                            data['outputControlPackage'][key] = True
                            break

        boundary_condition = data.pop('boundary_condition', None)
        if boundary_condition is not None:
            data['specifiedHeadBoundaryPackages'] = {"BFH": False, "CHD": False, "FHB": False, "otherPackages": ""}
            for key in data['specifiedHeadBoundaryPackages']:
                for pkg in boundary_condition['specified_head_boundary_packages']:
                    if pkg['description'] == key:
                        data['specifiedHeadBoundaryPackages'][key] = True
                        break

            if boundary_condition['other_specified_head_boundary_packages']:
                data['specifiedHeadBoundaryPackages']["otherPackages"] = boundary_condition[
                    'other_specified_head_boundary_packages']

            data['specifiedFluxBoundaryPackages'] = {"RCH": False, "WEL": False, "FHB": False, "otherPackages": ""}
            for key in data['specifiedFluxBoundaryPackages']:
                for pkg in boundary_condition['specified_flux_boundary_packages']:
                    if pkg['description'] == key:
                        data['specifiedFluxBoundaryPackages'][key] = True
                        break

            if boundary_condition['other_specified_flux_boundary_packages']:
                data['specifiedFluxBoundaryPackages']["otherPackages"] = boundary_condition[
                    'other_specified_flux_boundary_packages']

            data['headDependentFluxBoundaryPackages'] = {"DAF": False, "DRN": False, "DRT": False,
                                                         "ETS": False, "EVT": False, "GHB": False,
                                                         "LAK": False, "RES": False, "RIP": False,
                                                         "RIV": False, "SFR": False, "STR": False,
                                                         "UZF": False, "DAFG": False, "MNW1": False,
                                                         "MNW2": False, "otherPackages": ""}
            for key in data['headDependentFluxBoundaryPackages']:
                for pkg in boundary_condition['head_dependent_flux_boundary_packages']:
                    if pkg['description'] == key:
                        data['headDependentFluxBoundaryPackages'][key] = True
                        break
            if boundary_condition['other_head_dependent_flux_boundary_packages']:
                data['headDependentFluxBoundaryPackages']["otherPackages"] = boundary_condition[
                    'other_head_dependent_flux_boundary_packages']

        return data

    def create_aggr_folder(self, mi_aggr, comp_res, logger):
        new_folder = "modflow-instance"
        # passing 'migrating_resource' as True so that folder can be created even in published resource
        ResourceFile.create_folder(comp_res, new_folder, migrating_resource=True)
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
                mi_aggr.add_resource_file(res_file)
                msg = "Added file {} to mi aggregation".format(res_file.file_name)
                self.stdout.write(self.style.SUCCESS(msg))

    def set_executed_by(self, mi_aggr, comp_res, logger):
        linked_res_id = comp_res.extra_data[self._EXECUTED_BY_EXTRA_META_KEY]
        try:
            linked_res = get_resource_by_shortkey(linked_res_id)
        except Exception as err:
            msg = "Linked resource (ID:{}) was not found. Error:{}".format(linked_res_id, str(err))
            logger.warning(msg)
            self.stdout.write(self.style.WARNING(msg))
            return

        # check the linked resource is a composite resource
        if linked_res.resource_type == 'CompositeResource':
            # get the mp aggregation
            mp_aggr = linked_res.modelprogramlogicalfile_set.first()
            if mp_aggr:
                # use the external mp aggregation for executed_by
                mi_aggr.metadata.executed_by = mp_aggr
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

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resource_counter = 0
        to_resource_type = 'CompositeResource'

        msg = "THERE ARE CURRENTLY {} MODFLOW INSTANCE RESOURCES PRIOR TO CONVERSION TO COMPOSITE RESOURCE.".format(
            MODFLOWModelInstanceResource.objects.count())
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))

        for mi_res in MODFLOWModelInstanceResource.objects.all().iterator():
            msg = "Migrating MODFLOW instance resource:{}".format(mi_res.short_id)
            self.stdout.write(self.style.SUCCESS(msg))

            # check resource exists on irods
            istorage = mi_res.get_irods_storage()
            if not istorage.exists(mi_res.root_path):
                err_msg = "MODFLOW instance resource not found in irods (ID: {})".format(mi_res.short_id)
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
                    err_msg = "Failed to convert MODFLOW instance resource (ID: {}). " \
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
                continue

            self.create_aggr_folder(mi_aggr=mi_aggr, comp_res=comp_res, logger=logger)

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
            # load the default MODFLOW instance meta schema - Note: this schema is used only for migration and
            # is not a template schema that the user can select using the UI for metadata editing
            meta_json_schema = json.loads(get_modflow_meta_schema())
            mi_aggr.metadata_schema_json = meta_json_schema
            mi_aggr.save()
            # generate the JSON metadata from the MODFLOW specific metadata
            metadata_json = self.generate_metadata_json(mi_metadata_obj)
            if metadata_json:
                mi_aggr.metadata.metadata_json = metadata_json
                mi_aggr.metadata.save()
                try:
                    jsonschema.Draft4Validator(meta_json_schema).validate(metadata_json)
                except jsonschema.ValidationError as err:
                    msg = 'Metadata validation failed as per schema for resource (ID:{}). Error:{}'
                    msg = msg.format(comp_res.short_id, str(err))
                    logger.error(msg)
                    self.stdout.write(self.style.ERROR(msg))

            # create aggregation level xml files
            mi_aggr.create_aggregation_xml_documents()
            msg = 'One model instance aggregation was created in resource (ID:{})'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))

            comp_res.extra_metadata['MIGRATED_FROM'] = 'MODFLOW Instance Resource'
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
            msg = 'MODFLOW instance resource (ID: {}) was converted to Composite Resource type'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
            print("_______________________________________________")

        if resource_counter > 0:
            msg = "{} MODFLOW INSTANCE RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE.".format(
                resource_counter)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))

        if MODFLOWModelInstanceResource.objects.all().count() > 0:
            msg = "NOT ALL MODFLOW INSTANCE RESOURCES WERE CONVERTED TO COMPOSITE RESOURCE TYPE"
            logger.error(msg)
            self.stdout.write(self.style.WARNING(msg))
            msg = "THERE ARE CURRENTLY {} MODFLOW INSTANCE RESOURCES AFTER CONVERSION.".format(
                MODFLOWModelInstanceResource.objects.all().count())
            logger.info(msg)
            self.stdout.write(self.style.WARNING(msg))
