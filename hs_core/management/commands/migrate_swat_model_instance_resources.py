import logging
import sys
import traceback

import jsonschema
from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag
from hs_core.models import CoreMetaData
from hs_file_types.models import ModelInstanceLogicalFile
from hs_swat_modelinstance.models import SWATModelInstanceResource
from hs_swat_modelinstance.serializers import SWATModelInstanceMetaDataSerializerMigration
from ..utils import (
    migrate_core_meta_elements, get_swat_meta_schema, move_files_and_folders_to_model_aggregation,
    set_executed_by,
)


class Command(BaseCommand):
    help = "Convert all SWAT model instance resources to composite resource with model instance aggregation"
    _EXECUTED_BY_EXTRA_META_KEY = 'EXECUTED_BY_RES_ID'
    _MIGRATION_ISSUE = "MIGRATION ISSUE:"

    def generate_metadata_json(self, swat_meta):
        """
        Generate swat metadata in JSON format from the metadata of the swat model instance metadata
        :param swat_meta: This is the original metadata object from the swat model instance resource
        """
        serializer = SWATModelInstanceMetaDataSerializerMigration(swat_meta)
        data = serializer.data
        # mapping of json based field names to swat meta db field names
        key_maps = {'modelInput': 'model_input', 'modelObjective': 'model_objective',
                    'modelParameter': 'model_parameter', 'modelMethod': 'model_method',
                    'simulationType': 'simulation_type'}
        for key, value in key_maps.items():
            data[key] = data.pop(value, None)
            if data[key] is None or not data[key]:
                data.pop(key)

        if 'modelInput' in data:
            model_input_fields = ('demSourceURL', 'numberOfHRUs', 'demResolution', 'demSourceName', 'watershedArea',
                                  'numberOfSubbasins', 'soilDataSourceURL', 'warmupPeriodValue', 'soilDataSourceName',
                                  'routingTimeStepType', 'landUseDataSourceURL', 'rainfallTimeStepType',
                                  'routingTimeStepValue', 'landUseDataSourceName', 'rainfallTimeStepValue',
                                  'simulationTimeStepType', 'simulationTimeStepValue')
            model_input = data['modelInput']
            for fld in model_input_fields:
                if model_input[fld] is None or not model_input[fld].strip():
                    model_input.pop(fld)

        if 'modelObjective' in data:
            model_objective = data['modelObjective']
            swat_model_objectives = model_objective['swat_model_objectives']
            other_objectives = model_objective['other_objectives'].strip()
            data['modelObjective'] = {"BMPs": False, "hydrology": False, "waterQuality": False,
                                      "climateLanduseChange": False}
            objective_to_json_field_map = {"BMPs": "BMPs", "hydrology": "Hydrology", "waterQuality": "Water quality",
                                           "climateLanduseChange": "Climate / Landuse Change"}
            for obj_fld in data['modelObjective']:
                for objective in swat_model_objectives:
                    if objective['description'] == objective_to_json_field_map[obj_fld]:
                        data['modelObjective'][obj_fld] = True
                        break
            if other_objectives:
                data['modelObjective']['otherObjectives'] = other_objectives

        if 'modelParameter' in data:
            model_parameter = data['modelParameter']
            model_parameters = model_parameter['model_parameters']
            other_parameters = model_parameter['other_parameters'].strip()
            data['modelParameter'] = {"fertilizer": False, "pointSource": False, "cropRotation": False,
                                      "tileDrainage": False, "tillageOperation": False, "irrigationOperation": False,
                                      "inletOfDrainingWatershed": False}

            param_to_json_field_map = {"cropRotation": "Crop rotation", "tileDrainage": "Tile drainage",
                                       "pointSource": "Point source", "fertilizer": "Fertilizer",
                                       "tillageOperation": "Tillage operation",
                                       "inletOfDrainingWatershed": "Inlet of draining watershed",
                                       "irrigationOperation": "Irrigation operation"}
            for param_fld in data['modelParameter']:
                for param in model_parameters:
                    if param['description'] == param_to_json_field_map[param_fld]:
                        data['modelParameter'][param_fld] = True
                        break
            if other_parameters:
                data['modelParameter']['otherParameters'] = other_parameters

        if 'modelMethod' in data:
            model_method_fields = ('flowRoutingMethod', 'petEstimationMethod', 'runoffCalculationMethod')
            model_method = data['modelMethod']
            for fld in model_method_fields:
                if model_method[fld] is None or not model_method[fld].strip():
                    model_method.pop(fld)

        if 'simulationType' in data:
            simulation_type_name = data['simulationType']['simulation_type_name'].strip()
            if simulation_type_name:
                data['simulationType'] = simulation_type_name
            else:
                data.pop('simulationType')

        return data

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resource_counter = 0
        err_resource_counter = 0
        to_resource_type = 'CompositeResource'
        swat_resource_count = SWATModelInstanceResource.objects.count()
        msg = "THERE ARE CURRENTLY {} SWAT MODEL INSTANCE RESOURCES TO MIGRATE TO COMPOSITE RESOURCE.".format(
            swat_resource_count)
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))

        for mi_res in SWATModelInstanceResource.objects.all().iterator():
            msg = "Migrating SWAT instance resource:{}".format(mi_res.short_id)
            self.stdout.write(self.style.SUCCESS(msg))
            self.stdout.flush()
            # check resource exists on irods
            istorage = mi_res.get_irods_storage()
            if not istorage.exists(mi_res.root_path):
                err_resource_counter += 1
                err_msg = "{}SWAT instance resource not found in iRODS (ID: {})"
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
                                                            logger=logger, aggr_name='swat-instance')
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

            # copy the resource level abstract to aggregation as extended metadata
            if comp_res.metadata.description is not None:
                abstract = comp_res.metadata.description.abstract.strip()
                if abstract:
                    mi_aggr.metadata.extra_metadata['description'] = abstract
                    mi_aggr.metadata.save()

            # move the resource level extra_metadata to aggregation extra_metadata
            if comp_res.extra_metadata:
                mi_aggr.metadata.extra_metadata.update(comp_res.extra_metadata)
                mi_aggr.metadata.save()
                comp_res.extra_metadata = {}
                comp_res.save()
            # copy the model specific metadata to the mi aggregation
            if mi_metadata_obj.model_output:
                mi_aggr.metadata.has_model_output = mi_metadata_obj.model_output.includes_output

            if self._EXECUTED_BY_EXTRA_META_KEY in comp_res.extra_data:
                if not set_executed_by(self, mi_aggr, comp_res, logger):
                    err_resource_counter += 1

            mi_aggr.save()
            # load the default SWAT instance meta schema - Note: this schema is used only for migration and
            # is not a template schema that the user can select using the UI for metadata editing
            meta_json_schema = get_swat_meta_schema()
            mi_aggr.metadata_schema_json = meta_json_schema

            mi_aggr.save()
            # generate the JSON metadata from the SWAT specific metadata
            try:
                metadata_json = self.generate_metadata_json(mi_metadata_obj)
            except Exception as err:
                err_resource_counter += 1
                msg = '{}Failed to migrate SWAT specific metadata for resource (ID:{}). Error:{}'
                msg = msg.format(self._MIGRATION_ISSUE, comp_res.short_id, str(err))
                logger.error(msg)
                self.stdout.write(self.style.ERROR(msg))
                self.stdout.flush()
                mi_metadata_obj.delete()
                continue

            # delete the instance of model instance metadata that was part of the original swat
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
                msg = '{}Failed to generate swat aggregation metadata for view for resource (ID:{}). Error:{}'
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
                msg = '{}Failed to generate swat aggregation metadata for edit for resource (ID:{}). Error:{}'
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

            comp_res.extra_metadata['MIGRATED_FROM'] = 'SWAT Model Instance Resource'
            comp_res.save()
            set_dirty_bag_flag(comp_res)
            resource_counter += 1
            msg = 'SWAT model instance resource (ID: {}) was migrated to Composite Resource'
            msg = msg.format(comp_res.short_id)
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
            print("_______________________________________________")
            self.stdout.flush()

        print("________________MIGRATION SUMMARY_________________")
        msg = "{} SWAT MODEL INSTANCE RESOURCES EXISTED PRIOR TO MIGRATION TO COMPOSITE RESOURCE".format(
            swat_resource_count)
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))

        msg = "{} SWAT MODEL INSTANCE RESOURCES HAD ISSUES DURING MIGRATION TO COMPOSITE RESOURCE".format(
            err_resource_counter)
        if err_resource_counter > 0:
            logger.info(msg)
            self.stdout.write(self.style.ERROR(msg))
        else:
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))

        msg = "{} SWAT MODEL INSTANCE RESOURCES WERE MIGRATED TO COMPOSITE RESOURCE".format(
            resource_counter)
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))

        swat_resource_count = SWATModelInstanceResource.objects.count()
        if swat_resource_count > 0:
            msg = "NOT ALL SWAT MODEL INSTANCE RESOURCES WERE MIGRATED TO COMPOSITE RESOURCE"
            logger.error(msg)
            self.stdout.write(self.style.WARNING(msg))
            msg = "THERE ARE CURRENTLY {} SWAT MODEL INSTANCE RESOURCES AFTER MIGRATION".format(
                swat_resource_count)
            logger.info(msg)
            self.stdout.write(self.style.WARNING(msg))
        else:
            msg = "ALL SWAT MODEL INSTANCE RESOURCES WERE MIGRATED TO COMPOSITE RESOURCE"
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
        self.stdout.flush()
