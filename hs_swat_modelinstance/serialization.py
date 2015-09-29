
import rdflib

from hs_core.serialization import GenericResourceMeta
from hs_swat_modelinstance.models import ExecutedBy, ModelObjective, SimulationType, ModelMethod, \
    ModelParameter, ModelInput
from hs_swat_modelinstance.forms import model_objective_choices, parameters_choices


MODEL_OBJECTIVE_CHOICES = [c[0] for c in model_objective_choices]
MODEL_PARAMETER_CHOICES = [p[0] for p in parameters_choices]

class SWATModelInstanceResourceMeta(GenericResourceMeta):

    def __init__(self):
        super(SWATModelInstanceResourceMeta, self).__init__()

        self.model_output = None
        self.executed_by = None  # Optional
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

        print("--- SWATModelInstanceResource ---")

        hsterms = rdflib.namespace.Namespace('http://hydroshare.org/terms/')

        # Get ModelOutput
        for s, p, o in self._rmeta_graph.triples((None, hsterms.ModelOutput, None)):
            # Get IncludesModelOutput
            model_output_lit = self._rmeta_graph.value(o, hsterms.IncludesModelOutput)
            if model_output_lit is None:
                msg = "IncludesModelOutput for ModelOutput was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.model_output = SWATModelInstanceResourceMeta.ModelOutput()
            self.model_output.includes_output = str(model_output_lit) == 'Yes'
            print("\t\t{0}".format(self.model_output))
        # Get ExecutedBy
        for s, p, o in self._rmeta_graph.triples((None, hsterms.ExecutedBy, None)):
            # Get ModelProgramName
            executed_by_name_lit = self._rmeta_graph.value(o, hsterms.ModelProgramName)
            if executed_by_name_lit is None:
                msg = "ModelProgramName for ExecutedBy was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.executed_by = SWATModelInstanceResourceMeta.ExecutedBy()
            self.executed_by.name = str(executed_by_name_lit)
            print("\t\t{0}".format(self.executed_by))
        # Get ModelObjective
        for s, p, o in self._rmeta_graph.triples((None, hsterms.ModelObjective, None)):
            self.model_objective = SWATModelInstanceResourceMeta.ModelObjective(str(o))
            print("\t\t{0}".format(self.model_objective))
        # Get SimulationType
        for s, p, o in self._rmeta_graph.triples((None, hsterms.SimulationType, None)):
            self.simulation_type = SWATModelInstanceResourceMeta.SimulationType()
            self.simulation_type.simulation_type_name = str(o)
            print("\t\t{0}".format(self.simulation_type))
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
            # Get PETEstimationMethod
            pet_method_lit = self._rmeta_graph.value(o, hsterms.PETEstimationMethod)
            if pet_method_lit is not None:
                self.model_method.PET_estimation_method = str(pet_method_lit)
            print("\t\t{0}".format(self.model_method))
        # Get ModelParameter
        for s, p, o in self._rmeta_graph.triples((None, hsterms.ModelParameter, None)):
            self.model_parameter = SWATModelInstanceResourceMeta.ModelParameter(str(o))
            print("\t\t{0}".format(self.model_parameter))
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
            simulation_time_step_type_lit = self._rmeta_graph.value(o, hsterms.simulationTimeStepType)
            if simulation_time_step_type_lit is not None:
                self.model_input.simulation_time_step_type = str(simulation_time_step_type_lit)
            # Get simulationTimeStepValue
            simulation_time_step_value_lit = self._rmeta_graph.value(o, hsterms.simulationTimeStepValue)
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
            # Get DEMResolution
            DEM_resolution_lit = self._rmeta_graph.value(o, hsterms.DEMResolution)
            if DEM_resolution_lit is not None:
                self.model_input.DEM_resolution = str(DEM_resolution_lit)
            # Get DEMSourceName
            DEM_source_name_lit = self._rmeta_graph.value(o, hsterms.DEMSourceName)
            if DEM_source_name_lit is not None:
                self.model_input.DEM_source_name = str(DEM_source_name_lit)
            # Get DEMSourceURL
            DEM_source_URL_lit = self._rmeta_graph.value(o, hsterms.DEMSourceURL)
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
            print("\t\t{0}".format(self.model_input))

    def write_metadata_to_resource(self, resource):
        """
        Write metadata to resource

        :param resource: RasterResource instance
        """
        super(SWATModelInstanceResourceMeta, self).write_metadata_to_resource(resource)

        if self.model_output:
            resource.metadata._model_output.update(includes_output=self.model_output.includes_output)
        if self.executed_by:
            executed_by = resource.metadata.executed_by
            if not executed_by:
                # Create
                ExecutedBy.create(content_object=resource.metadata,
                                  name=self.executed_by.name)
            else:
                # Update
                ExecutedBy.update(executed_by.element_id,
                                  name=self.executed_by.name)
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
                # Create
                ModelObjective.create(content_object=resource.metadata,
                                      swat_model_objectives=swat_model_objectives,
                                      other_objectives=other_objectives_str)
            else:
                # Update
                ModelObjective.update(model_objective.element_id,
                                      swat_model_objectives=swat_model_objectives,
                                      other_objectives=other_objectives_str)
        if self.simulation_type:
            simulation_type = resource.metadata.simulation_type
            if not simulation_type:
                # Create
                SimulationType.create(content_object=resource.metadata,
                                      simulation_type_name=self.simulation_type.simulation_type_name)
            else:
                # Update
                SimulationType.update(simulation_type.element_id,
                                      simulation_type_name=self.simulation_type.simulation_type_name)
        if self.model_method:
            model_method = resource.metadata.model_method
            if not model_method:
                # Create
                ModelMethod.create(content_object=resource.metadata,
                                   runoff_calculation_method=self.model_method.runoff_calculation_method,
                                   flow_routing_method=self.model_method.flow_routing_method,
                                   PET_estimation_method=self.model_method.PET_estimation_method)
            else:
                #Update
                ModelMethod.create(model_method.element_id,
                                   runoff_calculation_method=self.model_method.runoff_calculation_method,
                                   flow_routing_method=self.model_method.flow_routing_method,
                                   PET_estimation_method=self.model_method.PET_estimation_method)
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
                # Create
                ModelParameter.create(content_object=resource.metadata,
                                      model_parameters=model_parameters,
                                      other_parameters=other_parameters_str)
            else:
                # Update
                ModelParameter.update(model_parameter.element_id,
                                      model_parameters=model_parameters,
                                      other_parameters=other_parameters_str)
        if self.model_input:
            model_input = resource.metadata.model_input
            if not model_input:
                # Create
                ModelInput.create(content_object=resource.metadata,
                                  warm_up_period=self.model_input.warm_up_period_value,
                                  rainfall_time_step_type=self.model_input.rainfall_time_step_type,
                                  rainfall_time_step_value=self.model_input.rainfall_time_step_value,
                                  routing_time_step_type=self.model_input.routing_time_step_type,
                                  routing_time_step_value=self.model_input.routing_time_step_value,
                                  simulation_time_step_type=self.model_input.simulation_time_step_type,
                                  simulation_time_step_value=self.model_input.simulation_time_step_value,
                                  watershed_area=self.model_input.watershed_area,
                                  number_of_subbasins=self.model_input.number_of_subbasins,
                                  number_of_HRUs=self.model_input.number_of_HRUs,
                                  DEM_resolution=self.model_input.DEM_resolution,
                                  DEM_source_name=self.model_input.DEM_source_name,
                                  DEM_source_URL=self.model_input.DEM_source_URL,
                                  landUse_data_source_name=self.model_input.landUse_data_source_name,
                                  landUse_data_source_URL=self.model_input.landUse_data_source_URL,
                                  soil_data_source_name=self.model_input.soil_data_source_name,
                                  soil_data_source_URL=self.model_input.soil_data_source_URL)
            else:
                # Update
                ModelInput.update(model_parameter.element_id,
                                  warm_up_period=self.model_input.warm_up_period_value,
                                  rainfall_time_step_type=self.model_input.rainfall_time_step_type,
                                  rainfall_time_step_value=self.model_input.rainfall_time_step_value,
                                  routing_time_step_type=self.model_input.routing_time_step_type,
                                  routing_time_step_value=self.model_input.routing_time_step_value,
                                  simulation_time_step_type=self.model_input.simulation_time_step_type,
                                  simulation_time_step_value=self.model_input.simulation_time_step_value,
                                  watershed_area=self.model_input.watershed_area,
                                  number_of_subbasins=self.model_input.number_of_subbasins,
                                  number_of_HRUs=self.model_input.number_of_HRUs,
                                  DEM_resolution=self.model_input.DEM_resolution,
                                  DEM_source_name=self.model_input.DEM_source_name,
                                  DEM_source_URL=self.model_input.DEM_source_URL,
                                  landUse_data_source_name=self.model_input.landUse_data_source_name,
                                  landUse_data_source_URL=self.model_input.landUse_data_source_URL,
                                  soil_data_source_name=self.model_input.soil_data_source_name,
                                  soil_data_source_URL=self.model_input.soil_data_source_URL)

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
            self.url = None  # Ignored for now as refactor is planned.

        def __str__(self):
            msg = "ExecutedBy name: {name}, url: {url}"
            msg = msg.format(name=self.name, url=self.name)
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class ModelObjective(object):

        def __init__(self):
            self.model_objectives = []  # Optional

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

        def __init__(self):
            self.model_parameters = []  # Optional

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
            self.warm_up_period_type = None  # Optional; Not implemented in hs_swat_modelinstance.models.ModelInput
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