import os
import logging

import rdflib

from django.db import transaction

from hs_core.serialization import GenericResourceMeta, HsDeserializationDependencyException
from hs_swat_modelinstance.models import ModelObjective, SimulationType, ModelMethod, \
    ModelParameter, ModelInput
from hs_swat_modelinstance.forms import model_objective_choices, parameters_choices


MODEL_OBJECTIVE_CHOICES = [c[0] for c in model_objective_choices]
MODEL_PARAMETER_CHOICES = [p[0] for p in parameters_choices]

logger = logging.getLogger(__name__)


class SWATModelInstanceResourceMeta(GenericResourceMeta):

    def __init__(self):
        super(SWATModelInstanceResourceMeta, self).__init__()

        self.model_output = None
        self.executed_by_name = None  # Optional
        self.executed_by_uri = None  # Optional
        self.model_objective = None  # Optional
        self.simulation_type = None
        self.model_method = None  # Optional
        self.model_parameter = None  # Optional
        self.model_input = None  # Optional

    def __str__(self):
        msg = "SWATModelInstanceResourceMeta"
        return msg

    def __unicode__(self):
        return unicode(str(self))

    def _read_resource_metadata(self):
        super(SWATModelInstanceResourceMeta, self)._read_resource_metadata()

        logger.debug("--- SWATModelInstanceResource ---")

        hsterms = rdflib.namespace.Namespace('http://hydroshare.org/terms/')

        # Get ModelOutput
        for s, p, o in self._rmeta_graph.triples((None, hsterms.ModelOutput, None)):
            # Get IncludesModelOutput
            model_output_lit = self._rmeta_graph.value(o, hsterms.includesModelOutput)
            if model_output_lit is None:
                msg = "includesModelOutput for ModelOutput was not found for resource {0}"\
                    .format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.model_output = SWATModelInstanceResourceMeta.ModelOutput()
            self.model_output.includes_output = str(model_output_lit) == 'Yes'
            logger.debug("\t\t{0}".format(self.model_output))
        # Get ExecutedBy
        # Should be hsterms.ExecutedBy, BUT THERE IS A TYPO IN THE XML!
        for s, p, o in self._rmeta_graph.triples((None, hsterms.ExecutedBY, None)):
            # Get modelProgramName
            executed_by_name_lit = self._rmeta_graph.value(o, hsterms.modelProgramName)
            if executed_by_name_lit is not None:
                self.executed_by_name = str(executed_by_name_lit)
            # Get modelProgramIdentifier
            executed_by_uri_lit = self._rmeta_graph.value(o, hsterms.modelProgramIdentifier)
            if executed_by_uri_lit is not None:
                self.executed_by_uri = str(executed_by_uri_lit)
            if (self.executed_by_name is not None) ^ (self.executed_by_uri is not None):
                msg = "Both modelProgramName and modelProgramIdentifier must be supplied if one " \
                      "is supplied."
                raise GenericResourceMeta.ResourceMetaException(msg)
        logger.debug("\t\tmodelProgramName {0}".format(str(self.executed_by_name)))
        logger.debug("\t\tmodelProgramIdentifier {0}".format(str(self.executed_by_uri)))
        # Get modelObjective
        for s, p, o in self._rmeta_graph.triples((None, hsterms.modelObjective, None)):
            self.model_objective = SWATModelInstanceResourceMeta.ModelObjective(str(o))
            logger.debug("\t\t{0}".format(self.model_objective))
        # Get simulationType
        for s, p, o in self._rmeta_graph.triples((None, hsterms.simulationType, None)):
            self.simulation_type = SWATModelInstanceResourceMeta.SimulationType()
            self.simulation_type.simulation_type_name = str(o)
            logger.debug("\t\t{0}".format(self.simulation_type))
        # Get ModelMethod
        for s, p, o in self._rmeta_graph.triples((None, hsterms.ModelMethod, None)):
            self.model_method = SWATModelInstanceResourceMeta.ModelMethod()
            # Get runoffCalculationMethod
            runoff_method_lit = self._rmeta_graph.value(o, hsterms.runoffCalculationMethod)
            if runoff_method_lit is not None:
                self.model_method.runoff_calculation_method = str(runoff_method_lit)
            # Get flowRoutingMethod
            flowrouting_method_lit = self._rmeta_graph.value(o, hsterms.flowRoutingMethod)
            if flowrouting_method_lit is not None:
                self.model_method.flow_routing_method = str(flowrouting_method_lit)
            # Get petEstimationMethod
            pet_method_lit = self._rmeta_graph.value(o, hsterms.petEstimationMethod)
            if pet_method_lit is not None:
                self.model_method.PET_estimation_method = str(pet_method_lit)
            logger.debug("\t\t{0}".format(self.model_method))
        # Get modelParameter
        for s, p, o in self._rmeta_graph.triples((None, hsterms.modelParameter, None)):
            self.model_parameter = SWATModelInstanceResourceMeta.ModelParameter(str(o))
            logger.debug("\t\t{0}".format(self.model_parameter))
        # Get ModelInput
        for s, p, o in self._rmeta_graph.triples((None, hsterms.ModelInput, None)):
            self.model_input = SWATModelInstanceResourceMeta.ModelInput()
            # Get warm-upPeriodType
            warmup_period_type_lit = self._rmeta_graph.value(o, hsterms['warm-upPeriodType'])
            if warmup_period_type_lit is not None:
                self.model_input.warm_up_period_type = str(warmup_period_type_lit)
            # Get warm-upPeriodValue
            warmup_period_value_lit = self._rmeta_graph.value(o, hsterms['warm-upPeriodValue'])
            if warmup_period_value_lit is not None:
                self.model_input.warm_up_period_value = str(warmup_period_value_lit)
            # Get rainfallTimeStepType
            rainfall_time_step_type_lit = self._rmeta_graph.value(o, hsterms.rainfallTimeStepType)
            if rainfall_time_step_type_lit is not None:
                self.model_input.rainfall_time_step_type = str(rainfall_time_step_type_lit)
            # Get rainfallTimeStepValue
            rainfall_time_step_value_lit = self._rmeta_graph.value(o, hsterms.rainfallTimeStepValue)
            if rainfall_time_step_value_lit is not None:
                self.model_input.rainfall_time_step_value = str(rainfall_time_step_value_lit)
            # Get routingTimeStepType
            routing_time_step_type_lit = self._rmeta_graph.value(o, hsterms.routingTimeStepType)
            if routing_time_step_type_lit is not None:
                self.model_input.routing_time_step_type = str(routing_time_step_type_lit)
            # Get routingTimeStepValue
            routing_time_step_value_lit = self._rmeta_graph.value(o, hsterms.routingTimeStepValue)
            if routing_time_step_value_lit is not None:
                self.model_input.routing_time_step_value = str(routing_time_step_value_lit)
            # Get simulationTimeStepType
            simulation_time_step_type_lit = self._rmeta_graph.value(o,
                                                                    hsterms.simulationTimeStepType)
            if simulation_time_step_type_lit is not None:
                self.model_input.simulation_time_step_type = str(simulation_time_step_type_lit)
            # Get simulationTimeStepValue
            simulation_time_step_value_lit = self._rmeta_graph.value(
                o,
                hsterms.simulationTimeStepValue)
            if simulation_time_step_value_lit is not None:
                self.model_input.simulation_time_step_value = str(simulation_time_step_value_lit)
            # Get watershedArea
            watershed_area_lit = self._rmeta_graph.value(o, hsterms.watershedArea)
            if watershed_area_lit is not None:
                self.model_input.watershed_area = str(watershed_area_lit)
            # Get numberOfSubbasins
            number_of_subbasins_lit = self._rmeta_graph.value(o, hsterms.numberOfSubbasins)
            if number_of_subbasins_lit is not None:
                self.model_input.number_of_subbasins = str(number_of_subbasins_lit)
            # Get numberOfHRUs
            number_of_HRUs_lit = self._rmeta_graph.value(o, hsterms.numberOfHRUs)
            if number_of_HRUs_lit is not None:
                self.model_input.number_of_HRUs = str(number_of_HRUs_lit)
            # Get demResolution
            DEM_resolution_lit = self._rmeta_graph.value(o, hsterms.demResolution)
            if DEM_resolution_lit is not None:
                self.model_input.DEM_resolution = str(DEM_resolution_lit)
            # Get demSourceName
            DEM_source_name_lit = self._rmeta_graph.value(o, hsterms.demSourceName)
            if DEM_source_name_lit is not None:
                self.model_input.DEM_source_name = str(DEM_source_name_lit)
            # Get demSourceURL
            DEM_source_URL_lit = self._rmeta_graph.value(o, hsterms.demSourceURL)
            if DEM_source_URL_lit is not None:
                self.model_input.DEM_source_URL = str(DEM_source_URL_lit)
            # Get landUseDataSourceName
            landUse_data_source_name_lit = self._rmeta_graph.value(o, hsterms.landUseDataSourceName)
            if landUse_data_source_name_lit is not None:
                self.model_input.landUse_data_source_name = str(landUse_data_source_name_lit)
            # Get landUseDataSourceURL
            landUse_data_source_URL_lit = self._rmeta_graph.value(o, hsterms.landUseDataSourceURL)
            if landUse_data_source_URL_lit is not None:
                self.model_input.landUse_data_source_URL = str(landUse_data_source_URL_lit)
            # Get soilDataSourceName
            soil_data_source_name_lit = self._rmeta_graph.value(o, hsterms.soilDataSourceName)
            if soil_data_source_name_lit is not None:
                self.model_input.soil_data_source_name = str(soil_data_source_name_lit)
            # Get soilDataSourceURL
            soil_data_source_URL_lit = self._rmeta_graph.value(o, hsterms.soilDataSourceURL)
            if soil_data_source_URL_lit is not None:
                self.model_input.soil_data_source_URL = str(soil_data_source_URL_lit)
            logger.debug("\t\t{0}".format(self.model_input))

    @transaction.atomic
    def write_metadata_to_resource(self, resource, **kwargs):
        """
        Write metadata to resource

        :param resource: RasterResource instance
        """
        super(SWATModelInstanceResourceMeta, self).write_metadata_to_resource(resource, **kwargs)

        if self.model_output is not None:
            if resource.metadata.model_output:
                resource.metadata.update_element('modeloutput', resource.metadata.model_output.id,
                                                 includes_output=self.model_output.includes_output)
            else:
                resource.metadata.create_element('modeloutput',
                                                 includes_output=self.model_output.includes_output)
        if self.executed_by_uri is not None:
            if resource.metadata.executed_by:
                # Remove existing
                resource.metadata._executed_by.all().delete()
            if self.executed_by_uri != 'None':
                # Only create ExecutedBy if URI is a URL.
                uri_stripped = self.executed_by_uri.strip('/')
                short_id = os.path.basename(uri_stripped)
                if short_id == '':
                    msg = "ExecutedBy URL {0} does not contain a model program resource ID, "
                    msg += "for resource {1}"
                    msg = msg.format(self.executed_by_uri, self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                try:
                    resource.metadata.create_element('ExecutedBy',
                                                     model_name=short_id)
                except Exception:
                    msg = "Creation of ExecutedBy failed, resource {0} may not exist.".format(
                        short_id)
                    raise HsDeserializationDependencyException(short_id, msg)

        if self.model_objective:
            swat_model_objectives = []
            other_objectives = []
            for obj in self.model_objective.model_objectives:
                if obj in MODEL_OBJECTIVE_CHOICES:
                    swat_model_objectives.append(obj)
                else:
                    other_objectives.append(obj)
            other_objectives_str = None
            if len(other_objectives) > 0:
                other_objectives_str = ",".join(other_objectives)
            model_objective = resource.metadata.model_objective
            if not model_objective:
                ModelObjective.create(content_object=resource.metadata,
                                      swat_model_objectives=swat_model_objectives,
                                      other_objectives=other_objectives_str)
            else:
                ModelObjective.update(model_objective.id,
                                      swat_model_objectives=swat_model_objectives,
                                      other_objectives=other_objectives_str)
        if self.simulation_type:
            simulation_type = resource.metadata.simulation_type
            if not simulation_type:
                SimulationType.create(
                    content_object=resource.metadata,
                    simulation_type_name=self.simulation_type.simulation_type_name
                )
            else:
                SimulationType.update(
                    simulation_type.id,
                    simulation_type_name=self.simulation_type.simulation_type_name
                )
        if self.model_method:
            model_method = resource.metadata.model_method
            if not model_method:
                ModelMethod.create(
                    content_object=resource.metadata,
                    runoffCalculationMethod=self.model_method.runoff_calculation_method,
                    flowRoutingMethod=self.model_method.flow_routing_method,
                    petEstimationMethod=self.model_method.PET_estimation_method
                )
            else:
                ModelMethod.update(
                    model_method.id,
                    runoffCalculationMethod=self.model_method.runoff_calculation_method,
                    flowRoutingMethod=self.model_method.flow_routing_method,
                    petEstimationMethod=self.model_method.PET_estimation_method
                )
        if self.model_parameter:
            model_parameters = []
            other_parameters = []
            for param in self.model_parameter.model_parameters:
                if param in MODEL_PARAMETER_CHOICES:
                    model_parameters.append(param)
                else:
                    other_parameters.append(param)
            other_parameters_str = None
            if len(other_parameters) > 0:
                other_parameters_str = ",".join(other_parameters)
            model_parameter = resource.metadata.model_parameter
            if not model_parameter:
                ModelParameter.create(content_object=resource.metadata,
                                      model_parameters=model_parameters,
                                      other_parameters=other_parameters_str)
            else:
                ModelParameter.update(model_parameter.id,
                                      model_parameters=model_parameters,
                                      other_parameters=other_parameters_str)
        if self.model_input:
            model_input = resource.metadata.model_input
            if not model_input:
                ModelInput.create(
                    content_object=resource.metadata,
                    warmupPeriodValue=self.model_input.warm_up_period_value,
                    rainfallTimeStepType=self.model_input.rainfall_time_step_type,
                    rainfallTimeStepValue=self.model_input.rainfall_time_step_value,
                    routingTimeStepType=self.model_input.routing_time_step_type,
                    routingTimeStepValue=self.model_input.routing_time_step_value,
                    simulationTimeStepType=self.model_input.simulation_time_step_type,
                    simulationTimeStepValue=self.model_input.simulation_time_step_value,
                    watershedArea=self.model_input.watershed_area,
                    numberOfSubbasins=self.model_input.number_of_subbasins,
                    numberOfHRUs=self.model_input.number_of_HRUs,
                    demResolution=self.model_input.DEM_resolution,
                    demSourceName=self.model_input.DEM_source_name,
                    demSourceURL=self.model_input.DEM_source_URL,
                    landUseDataSourceName=self.model_input.landUse_data_source_name,
                    landUseDataSourceURL=self.model_input.landUse_data_source_URL,
                    soilDataSourceName=self.model_input.soil_data_source_name,
                    soilDataSourceURL=self.model_input.soil_data_source_URL
                )
            else:
                ModelInput.update(
                    model_input.id,
                    warmupPeriodValue=self.model_input.warm_up_period_value,
                    rainfallTimeStepType=self.model_input.rainfall_time_step_type,
                    rainfallTimeStepValue=self.model_input.rainfall_time_step_value,
                    routingTimeStepType=self.model_input.routing_time_step_type,
                    routingTimeStepValue=self.model_input.routing_time_step_value,
                    simulationTimeStepType=self.model_input.simulation_time_step_type,
                    simulationTimeStepValue=self.model_input.simulation_time_step_value,
                    watershedArea=self.model_input.watershed_area,
                    numberOfSubbasins=self.model_input.number_of_subbasins,
                    numberOfHRUs=self.model_input.number_of_HRUs,
                    demResolution=self.model_input.DEM_resolution,
                    demSourceName=self.model_input.DEM_source_name,
                    demSourceURL=self.model_input.DEM_source_URL,
                    landUseDataSourceName=self.model_input.landUse_data_source_name,
                    landUseDataSourceURL=self.model_input.landUse_data_source_URL,
                    soilDataSourceName=self.model_input.soil_data_source_name,
                    soilDataSourceURL=self.model_input.soil_data_source_URL
                )

    class ModelOutput(object):

        def __init__(self):
            self.includes_output = False

        def __str__(self):
            msg = "ModelOutput includes_output: {includes_output}"
            msg = msg.format(includes_output=self.includes_output)
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class ExecutedBy(object):

        def __init__(self):
            self.name = None
            self.url = None

        def __str__(self):
            msg = "ExecutedBy name: {name}, url: {url}"
            msg = msg.format(name=self.name, url=self.name)
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class ModelObjective(object):

        def __init__(self, model_objects_str):
            self.model_objectives = [o.strip() for o in model_objects_str.split(',')]

        def __str__(self):
            msg = "ModelObjective model_objectives: {model_objectives}"
            msg = msg.format(model_objectives=str(self.model_objectives))
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class SimulationType(object):

        def __init__(self):
            self.simulation_type_name = None

        def __str__(self):
            msg = "SimulationType simulation_type_name: {simulation_type_name}"
            msg = msg.format(simulation_type_name=self.simulation_type_name)
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class ModelMethod(object):

        def __init__(self):
            self.runoff_calculation_method = None  # Optional
            self.flow_routing_method = None  # Optional
            self.PET_estimation_method = None  # Optional

        def __str__(self):
            msg = "ModelMethod runoff_calculation_method: {runoff_calculation_method}, "
            msg += "flow_routing_method: {flow_routing_method}, "
            msg += "PET_estimation_method: {PET_estimation_method}"
            msg = msg.format(runoff_calculation_method=self.runoff_calculation_method,
                             flow_routing_method=self.flow_routing_method,
                             PET_estimation_method=self.PET_estimation_method)
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class ModelParameter(object):

        def __init__(self, model_parameters_str):
            self.model_parameters = [p.strip() for p in model_parameters_str.split(',')]

        def __str__(self):
            msg = "ModelParameter model_parameters: {model_parameters}"
            msg = msg.format(model_parameters=str(self.model_parameters))
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class ModelInput(object):

        def __init__(self):
            self.warm_up_period_type = None  # Opt;Not in hs_swat_modelinstance.models.ModelInput
            self.warm_up_period_value = None  # Optional
            self.rainfall_time_step_type = None  # Optional
            self.rainfall_time_step_value = None  # Optional
            self.routing_time_step_type = None  # Optional
            self.routing_time_step_value = None  # Optional
            self.simulation_time_step_type = None  # Optional
            self.simulation_time_step_value = None  # Optional
            self.watershed_area = None  # Optional
            self.number_of_subbasins = None  # Optional
            self.number_of_HRUs = None  # Optional
            self.DEM_resolution = None  # Optional
            self.DEM_source_name = None  # Optional
            self.DEM_source_URL = None  # Optional
            self.landUse_data_source_name = None  # Optional
            self.landUse_data_source_URL = None  # Optional
            self.soil_data_source_name = None  # Optional
            self.soil_data_source_URL = None  # Optional

        def __str__(self):
            msg = "ModelInput warm_up_period_type: {warm_up_period_type}, "
            msg += "warm_up_period_value: {warm_up_period_value}, "
            msg += "rainfall_time_step_type: {rainfall_time_step_type}, "
            msg += "rainfall_time_step_value: {rainfall_time_step_value}, "
            msg += "routing_time_step_type: {routing_time_step_type}, "
            msg += "routing_time_step_value: {routing_time_step_value}, "
            msg += "simulation_time_step_type: {simulation_time_step_type}, "
            msg += "simulation_time_step_value: {simulation_time_step_value}, "
            msg += "watershed_area: {watershed_area}, number_of_subbasins: {number_of_subbasins}, "
            msg += "number_of_HRUs: {number_of_HRUs}, DEM_resolution: {DEM_resolution}, "
            msg += "DEM_source_name: {DEM_source_name}, DEM_source_URL: {DEM_source_URL}, "
            msg += "landUse_data_source_name: {landUse_data_source_name}, "
            msg += "landUse_data_source_URL: {landUse_data_source_URL}, "
            msg += "soil_data_source_name: {soil_data_source_name}, "
            msg += "soil_data_source_URL: {soil_data_source_URL}"
            msg = msg.format(warm_up_period_type=self.warm_up_period_type,
                             warm_up_period_value=self.warm_up_period_value,
                             rainfall_time_step_type=self.rainfall_time_step_type,
                             rainfall_time_step_value=self.rainfall_time_step_value,
                             routing_time_step_type=self.routing_time_step_type,
                             routing_time_step_value=self.routing_time_step_value,
                             simulation_time_step_type=self.simulation_time_step_type,
                             simulation_time_step_value=self.simulation_time_step_value,
                             watershed_area=self.watershed_area,
                             number_of_subbasins=self.number_of_subbasins,
                             number_of_HRUs=self.number_of_HRUs,
                             DEM_resolution=self.DEM_resolution,
                             DEM_source_name=self.DEM_source_name,
                             DEM_source_URL=self.DEM_source_URL,
                             landUse_data_source_name=self.landUse_data_source_name,
                             landUse_data_source_URL=self.landUse_data_source_URL,
                             soil_data_source_name=self.soil_data_source_name,
                             soil_data_source_URL=self.soil_data_source_URL)
            return msg

        def __unicode__(self):
            return unicode(str(self))
