import logging
import sys
import traceback

import jsonschema
from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag
from hs_core.models import CoreMetaData
from hs_file_types.models import ModelInstanceLogicalFile
from hs_modflow_modelinstance.models import MODFLOWModelInstanceResource
from hs_modflow_modelinstance.serializers import MODFLOWModelInstanceMetaDataSerializerMigration
from ..utils import (
    migrate_core_meta_elements, get_modflow_meta_schema, move_files_and_folders_to_model_aggregation,
    set_executed_by,
)


class Command(BaseCommand):
    help = "Convert all MODFLOW model instance resources to composite resource with model instance aggregation"
    _EXECUTED_BY_EXTRA_META_KEY = 'EXECUTED_BY_RES_ID'
    _MIGRATION_ISSUE = "MIGRATION ISSUE:"

    def generate_metadata_json(self, modflow_meta):
        """
        Generate modflow metadata in JSON format from the metadata of the modflow model instance metadata
        :param modflow_meta: This is the original metadata object from the modflow model instance resource
        """
        serializer = MODFLOWModelInstanceMetaDataSerializerMigration(modflow_meta)
        data = serializer.data
        # mapping of json based field names to modflow meta db field names
        key_maps = {'studyArea': 'study_area', 'modelCalibration': 'model_calibration',
                    'groundwaterFlow': 'ground_water_flow', 'gridDimensions': 'grid_dimensions',
                    'stressPeriod': 'stress_period', 'modelInputs': 'model_inputs'}

        for key, value in key_maps.items():
            data[key] = data.pop(value, None)
            if data[key] is None or not data[key]:
                data.pop(key)

        if 'studyArea' in data:
            study_area_fields = ('totalWidth', 'totalLength', 'maximumElevation', 'minimumElevation')
            study_area = data['studyArea']
            for fld in study_area_fields:
                if study_area[fld] is None or not study_area[fld].strip():
                    study_area.pop(fld)

        if 'groundwaterFlow' in data:
            ground_water_flow_fields = ('flowPackage', 'flowParameter', 'unsaturatedZonePackage',
                                        'seawaterIntrusionPackage', 'horizontalFlowBarrierPackage')
            ground_water_flow = data['groundwaterFlow']
            for fld in ground_water_flow_fields:
                if ground_water_flow[fld] is None:
                    ground_water_flow.pop(fld)
                elif isinstance(ground_water_flow[fld], str) and not ground_water_flow[fld].strip():
                    ground_water_flow.pop(fld)

        if 'gridDimensions' in data:
            grid_fields = ('typeOfRows', 'numberOfRows', 'typeOfColumns', 'numberOfColumns', 'numberOfLayers')
            grid = data['gridDimensions']
            for fld in grid_fields:
                if grid[fld] is None or not grid[fld].strip():
                    grid.pop(fld)

        if 'modelCalibration' in data:
            model_fields = ('observationType', 'calibrationMethod', 'calibratedParameter', 'observationProcessPackage')
            model_calibration = data['modelCalibration']
            for fld in model_fields:
                if model_calibration[fld] is None or not model_calibration[fld].strip():
                    model_calibration.pop(fld)

        if 'modelInputs' in data:
            model_fields = ('inputType', 'inputSourceName', 'inputSourceURL')
            model_inputs = data['modelInputs']
            for model_input in model_inputs:
                for fld in model_fields:
                    if model_input[fld] is None or not model_input[fld].strip():
                        model_input.pop(fld)

        general_elements = data.pop('general_elements', None)
        if general_elements is not None:
            data['modelSolver'] = general_elements['modelSolver']
            if data['modelSolver'] is None or not data['modelSolver'].strip():
                data.pop('modelSolver')
            data['modelParameter'] = general_elements['modelParameter']
            if data['modelParameter'] is None or not data['modelParameter'].strip():
                data.pop('modelParameter')
            data['subsidencePackage'] = general_elements['subsidencePackage']
            if data['subsidencePackage'] is None or not data['subsidencePackage'].strip():
                data.pop('subsidencePackage')

            output_control_pkg = general_elements['output_control_package']
            if output_control_pkg:
                data['outputControlPackage'] = {'OC': False, 'HYD': False, 'GAGE': False, 'LMT6': False, 'MNWI': False}
                for key in data['outputControlPackage']:
                    for pkg in output_control_pkg:
                        if pkg['description'] == key:
                            data['outputControlPackage'][key] = True
                            break

        if 'stressPeriod' in data:
            stress_period_fields = ('stressPeriodType', 'steadyStateValue', 'transientStateValueType',
                                    'transientStateValue')
            for fld in stress_period_fields:
                if fld in list(data['stressPeriod']):
                    new_key = ""
                    v = data['stressPeriod'].pop(fld)
                    if v is None or not v.strip():
                        continue
                    if fld == 'stressPeriodType':
                        new_key = 'type'
                    elif fld == 'steadyStateValue':
                        new_key = 'lengthOfSteadyStateStressPeriod'
                    elif fld == 'transientStateValueType':
                        new_key = 'typeOfTransientStateStressPeriod'
                    elif fld == 'transientStateValue':
                        new_key = 'lengthOfTransientStateStressPeriod'
                    if new_key:
                        data['stressPeriod'][new_key] = v

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

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resource_counter = 0
        err_resource_counter = 0
        to_resource_type = 'CompositeResource'
        modflow_resource_count = MODFLOWModelInstanceResource.objects.count()
        msg = "THERE ARE CURRENTLY {} MODFLOW MODEL INSTANCE RESOURCES TO MIGRATE TO COMPOSITE RESOURCE.".format(
            modflow_resource_count)
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))

        for mi_res in MODFLOWModelInstanceResource.objects.all().iterator():
            msg = "Migrating MODFLOW instance resource:{}".format(mi_res.short_id)
            self.stdout.write(self.style.SUCCESS(msg))
            self.stdout.flush()
            # check resource exists on irods
            istorage = mi_res.get_irods_storage()
            if not istorage.exists(mi_res.root_path):
                err_resource_counter += 1
                err_msg = "{}MODFLOW instance resource not found in iRODS (ID: {})"
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
                                                            logger=logger, aggr_name='modflow-model-instance')
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
            # load the default MODFLOW instance meta schema - Note: this schema is used only for migration and
            # is not a template schema that the user can select using the UI for metadata editing
            meta_json_schema = get_modflow_meta_schema()
            mi_aggr.metadata_schema_json = meta_json_schema

            mi_aggr.save()
            # generate the JSON metadata from the MODFLOW specific metadata
            try:
                metadata_json = self.generate_metadata_json(mi_metadata_obj)
            except Exception as err:
                err_resource_counter += 1
                msg = '{}Failed to migrate MODFLOW specific metadata for resource (ID:{}). Error:{}'
                msg = msg.format(self._MIGRATION_ISSUE, comp_res.short_id, str(err))
                logger.error(msg)
                self.stdout.write(self.style.ERROR(msg))
                self.stdout.flush()
                mi_metadata_obj.delete()
                continue

            # delete the instance of model instance metadata that was part of the original modflow
            # model instance resource
            mi_metadata_obj.delete()

            if metadata_json:
                mi_aggr.metadata.metadata_json = metadata_json
                mi_aggr.metadata.save()
                try:
                    jsonschema.Draft4Validator(meta_json_schema).validate(metadata_json)
                except jsonschema.ValidationError as err:
                    err_resource_counter += 1
                    msg = '{}Metadata validation failed as per schema for resource (ID:{}). Error:{}'
                    msg = msg.format(self._MIGRATION_ISSUE, comp_res.short_id, str(err))
                    logger.error(msg)
                    self.stdout.write(self.style.ERROR(msg))
                    self.stdout.flush()
                    continue

            try:
                mi_aggr.metadata.get_html()
            except Exception as err:
                err_resource_counter += 1
                traceback.print_exception(*sys.exc_info())
                msg = '{}Failed to generate modflow aggregation metadata for view for resource (ID:{}). Error:{}'
                msg = msg.format(self._MIGRATION_ISSUE, comp_res.short_id, str(err))
                logger.error(msg)
                self.stdout.write(self.style.ERROR(msg))
                self.stdout.flush()
                continue

            try:
                mi_aggr.metadata.get_html_forms()
            except Exception as err:
                err_resource_counter += 1
                traceback.print_exception(*sys.exc_info())
                msg = '{}Failed to generate modflow aggregation metadata for edit for resource (ID:{}). Error:{}'
                msg = msg.format(self._MIGRATION_ISSUE, comp_res.short_id, str(err))
                logger.error(msg)
                self.stdout.write(self.style.ERROR(msg))
                self.stdout.flush()
                continue

            mi_aggr.set_metadata_dirty()
            msg = 'One model instance aggregation was created in resource (ID:{})'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))

            comp_res.extra_metadata['MIGRATED_FROM'] = 'MODFLOW Instance Resource'
            comp_res.save()
            set_dirty_bag_flag(comp_res)
            resource_counter += 1
            msg = 'MODFLOW model instance resource (ID: {}) was migrated to Composite Resource'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
            print("_______________________________________________")
            self.stdout.flush()

        print("________________MIGRATION SUMMARY_________________")
        msg = "{} MODFLOW MODEL INSTANCE RESOURCES EXISTED PRIOR TO MIGRATION TO COMPOSITE RESOURCE".format(
            modflow_resource_count)
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))

        msg = "{} MODFLOW MODEL INSTANCE RESOURCES HAD ISSUES DURING MIGRATION TO COMPOSITE RESOURCE".format(
            err_resource_counter)
        if err_resource_counter > 0:
            logger.info(msg)
            self.stdout.write(self.style.ERROR(msg))
        else:
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))

        msg = "{} MODFLOW MODEL INSTANCE RESOURCES WERE MIGRATED TO COMPOSITE RESOURCE".format(
            resource_counter)
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))

        modflow_resource_count = MODFLOWModelInstanceResource.objects.count()
        if modflow_resource_count > 0:
            msg = "NOT ALL MODFLOW MODEL INSTANCE RESOURCES WERE MIGRATED TO COMPOSITE RESOURCE"
            logger.error(msg)
            self.stdout.write(self.style.WARNING(msg))
            msg = "THERE ARE CURRENTLY {} MODFLOW MODEL INSTANCE RESOURCES AFTER MIGRATION".format(
                modflow_resource_count)
            logger.info(msg)
            self.stdout.write(self.style.WARNING(msg))
        else:
            msg = "ALL MODFLOW MODEL INSTANCE RESOURCES WERE MIGRATED TO COMPOSITE RESOURCE"
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
        self.stdout.flush()
