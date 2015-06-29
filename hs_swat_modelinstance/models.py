__author__ = 'Mohamed Morsy'
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.auth.models import User, Group
from django.db import models
from mezzanine.pages.models import Page, RichText
from mezzanine.core.models import Ownable
from mezzanine.pages.page_processors import processor_for
from lxml import etree
from hs_core.models import AbstractResource, resource_processor, CoreMetaData, AbstractMetaDataElement




# extended metadata elements for SWAT Model Instance resource type
class ModelOutput(AbstractMetaDataElement):
    term = 'ModelOutput'
    includes_output = models.BooleanField(default=False)

    @classmethod
    def create(cls, **kwargs):
        return ModelOutput.objects.create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        model_output = ModelOutput.objects.get(id=element_id)
        if model_output:
            for key, value in kwargs.iteritems():
                setattr(model_output, key, value)

            model_output.save()
        else:
            raise ObjectDoesNotExist("No ModelOutput element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ModelOutput element of a resource can't be deleted.")


class ExecutedBy(AbstractMetaDataElement):
    term = 'ExecutedBY'
    name = models.CharField(max_length=200)
    url = models.URLField()

    def __unicode__(self):
        self.name

    @classmethod
    def create(cls, **kwargs):
        return ExecutedBy.objects.create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        executed_by = ExecutedBy.objects.get(id=element_id)
        if executed_by:
            for key, value in kwargs.iteritems():
                setattr(executed_by, key, value)

            executed_by.save()
        else:
            raise ObjectDoesNotExist("No ExecutedBy element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ExecutedBy element of a resource can't be deleted.")


class ModelObjectiveChoices(models.Model):
    description = models.CharField(max_length=300)

    def __unicode__(self):
        self.description

class ModelObjective(AbstractMetaDataElement):
    term = 'ModelObjective'
    swat_model_objectives = models.ManyToManyField(ModelObjectiveChoices, null=True, blank=True)
    other_objectives = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        self.other_objectives

    def get_swat_model_objectives(self):
        return ', '.join([objective.description for objective in self.swat_model_objectives.all()])

    @classmethod
    def create(cls, **kwargs):
        if 'swat_model_objectives' in kwargs:
            cls._validate_swat_model_objectives(kwargs['swat_model_objectives'])
        else:
            raise ValidationError("swat_model_objectives is missing.")
        if not 'other_objectives' in kwargs:
            raise ValidationError("modelObjective other_objectives is missing.")

        metadata_obj = kwargs['content_object']
        model_objective = ModelObjective.objects.create(other_objectives=kwargs['other_objectives'],
                                                        content_object=metadata_obj)
        for swat_objective in kwargs['swat_model_objectives']:
            qs = ModelObjectiveChoices.objects.filter(description__iexact=swat_objective)
            if qs.exists():
                model_objective.swat_model_objectives.add(qs[0])
            else:
                model_objective.swat_model_objectives.create(description=swat_objective)

        return model_objective

    @classmethod
    def update(cls, element_id, **kwargs):
        model_objective = ModelObjective.objects.get(id=element_id)
        if model_objective:
            if 'swat_model_objectives' in kwargs:
                cls._validate_swat_model_objectives(kwargs['swat_model_objectives'])
                model_objective.swat_model_objectives.all().delete()
                for swat_objective in kwargs['swat_model_objectives']:
                    qs = ModelObjectiveChoices.objects.filter(description__iexact=swat_objective)
                    if qs.exists():
                        model_objective.swat_model_objectives.add(qs[0])
                    else:
                        model_objective.swat_model_objectives.create(description=swat_objective)

            if 'other_objectives' in kwargs:
                model_objective.other_objectives = kwargs['other_objectives']

            model_objective.save()

            # delete model_objective metadata element if it has no data
            if len(model_objective.swat_model_objectives.all()) == 0 and len(model_objective.other_objectives) == 0:
                model_objective.delete()
        else:
            raise ObjectDoesNotExist("No ModelObjective element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ModelObjective element of a resource can't be deleted.")

    @classmethod
    def _validate_swat_model_objectives(cls, objectives):
        for swat_objective in objectives:
            if swat_objective not in ['Hydrology', 'Water quality', 'BMPs', 'Climate / Landuse Change', 'Other']:
                raise ValidationError('Invalid swat_model_objectives:%s' % objectives)

# TODO: change the class name to: SimulationType
class simulationType(AbstractMetaDataElement):
    term = 'simulationType'
    type_choices = (('Normal Simulation', 'Normal Simulation'), ('Sensitivity Analysis', 'Sensitivity Analysis'),
                    ('Auto-Calibration', 'Auto-Calibration'))
    simulation_type_name = models.CharField(max_length=100, choices=type_choices, verbose_name='Simulation type')

    def __unicode__(self):
        self.simulation_type_name

    @classmethod
    def create(cls, **kwargs):
        if 'simulation_type_name' in kwargs:
            if not kwargs['simulation_type_name'] in ['Normal Simulation', 'Sensitivity Analysis', 'Auto-Calibration']:
                raise ValidationError('Invalid simulation type:%s' % kwargs['type'])
        else:
            raise ValidationError("simulation type is missing.")

        metadata_obj = kwargs['content_object']
        return simulationType.objects.create(simulation_type_name=kwargs['simulation_type_name'], content_object=metadata_obj)

    @classmethod
    def update(cls, element_id, **kwargs):
        simulation_type = simulationType.objects.get(id=element_id)
        if simulation_type:
            for key, value in kwargs.iteritems():
                if key in ('simulation_type_name'):
                    setattr(simulation_type, key, value)
            simulation_type.save()
        else:
            raise ObjectDoesNotExist("No simulationType element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("simulationType element of a resource can't be deleted.")

class ModelMethods(AbstractMetaDataElement):
    term = 'ModelMethods'
    runoff_calculation_method = models.CharField(max_length=200, null=True, blank=True)
    flow_routing_method = models.CharField(max_length=200, null=True, blank=True)
    PET_estimation_method = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        self.runoff_calculation_method

    @classmethod
    def create(cls, **kwargs):
        if not 'runoff_calculation_method' in kwargs:
            raise ValidationError("modelMethods runoffCalculationMethod is missing.")
        if not 'flow_routing_method' in kwargs:
            raise ValidationError("modelMethods flowRoutingMethod is missing.")
        if not 'PET_estimation_method' in kwargs:
            raise ValidationError("modelMethods PETestimationMethod is missing.")
        metadata_obj = kwargs['content_object']
        return ModelMethods.objects.create(runoff_calculation_method=kwargs['runoff_calculation_method'],
                                             flow_routing_method=kwargs['flow_routing_method'],
                                             PET_estimation_method=kwargs['PET_estimation_method'],
                                             content_object=metadata_obj)

    @classmethod
    def update(cls, element_id, **kwargs):
        model_methods = ModelMethods.objects.get(id=element_id)
        if model_methods:
            for key, value in kwargs.iteritems():
                if key in ('runoff_calculation_method', 'flow_routing_method', 'PET_estimation_method'):
                    setattr(model_methods, key, value)
            model_methods.save()
        else:
            raise ObjectDoesNotExist("No ModelMethods element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ModelMethods element of a resource can't be deleted.")


class ModelParametersChoices(models.Model):
    description = models.CharField(max_length=300)

    def __unicode__(self):
        self.description

class SWATModelParameters(AbstractMetaDataElement):
    term = 'SWATModelParameters'
    model_parameters = models.ManyToManyField(ModelParametersChoices, null=True, blank=True)
    other_parameters = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        self.other_parameters

    def get_swat_model_parameters(self):
        return ', '.join([parameter.description for parameter in self.model_parameters.all()])

    @classmethod
    def create(cls, **kwargs):
        if 'model_parameters' in kwargs:
            cls._validate_swat_model_parameters(kwargs['model_parameters'])
        else:
            raise ValidationError("model_parameters is missing.")
        if not 'other_parameters' in kwargs:
            raise ValidationError("SWATModelParameters other_parameters is missing.")

        metadata_obj = kwargs['content_object']
        swat_model_parameters = SWATModelParameters.objects.create(other_parameters=kwargs['other_parameters'],
                                                  content_object=metadata_obj)

        for swat_parameter in kwargs['model_parameters']:
            qs = ModelParametersChoices.objects.filter(description__iexact=swat_parameter)
            if qs.exists():
                swat_model_parameters.model_parameters.add(qs[0])
            else:
                swat_model_parameters.model_parameters.create(description=swat_parameter)

        return swat_model_parameters

    @classmethod
    def update(cls, element_id, **kwargs):
        swat_model_parameters = SWATModelParameters.objects.get(id=element_id)
        if swat_model_parameters:
            if 'model_parameters' in kwargs:
                cls._validate_swat_model_parameters(kwargs['model_parameters'])
                swat_model_parameters.model_parameters.all().delete()
                for swat_parameter in kwargs['model_parameters']:
                    qs = ModelParametersChoices.objects.filter(description__iexact=swat_parameter)
                    if qs.exists():
                        swat_model_parameters.model_parameters.add(qs[0])
                    else:
                        swat_model_parameters.model_parameters.create(description=swat_parameter)

            if 'other_parameters' in kwargs:
                swat_model_parameters.other_parameters = kwargs['other_parameters']

            swat_model_parameters.save()

            # delete model_parameters metadata element if it has no data
            if len(swat_model_parameters.model_parameters.all()) == 0 and len(swat_model_parameters.other_parameters) == 0:
                swat_model_parameters.delete()
        else:
            raise ObjectDoesNotExist("No SWATModelParameters element was found for the provided id:%s" % kwargs['id'])


    @classmethod
    def remove(cls, element_id):
        raise ValidationError("SWATModelParameters element of a resource can't be deleted.")

    @classmethod
    def _validate_swat_model_parameters(cls, parameters):
        for swat_parameters in parameters:
            if swat_parameters not in ['Crop rotation', 'Tile drainage', 'Point source', 'Fertilizer', 'Tillage operation', 'Inlet of draining watershed', 'Irrigation operation']:
                raise ValidationError('Invalid swat_model_parameters:%s' % parameters)

class ModelInput(AbstractMetaDataElement):
    term = 'ModelInput'
    warm_up_period = models.CharField(max_length=100, null=True, blank=True, verbose_name='Warm-up period in years')
    rainfall_time_step = models.CharField(max_length=100, null=True, blank=True)
    routing_time_step = models.CharField(max_length=100, null=True, blank=True)
    simulation_time_step = models.CharField(max_length=100, null=True, blank=True)
    watershed_area = models.CharField(max_length=100, null=True, blank=True, verbose_name='Waterhsed area in square kilometers')
    number_of_subbasins = models.CharField(max_length=100, null=True, blank=True)
    number_of_HRUs = models.CharField(max_length=100, null=True, blank=True)
    DEM_resolution = models.CharField(max_length=100, null=True, blank=True, verbose_name='DEM resolution in meters')
    DEM_source_name = models.CharField(max_length=200, null=True, blank=True)
    DEM_source_URL = models.URLField(null=True, blank=True)
    landUse_data_source_name = models.CharField(max_length=200, null=True, blank=True)
    landUse_data_source_URL = models.URLField(null=True, blank=True)
    soil_data_source_name = models.CharField(max_length=200, null=True, blank=True)
    soil_data_source_URL = models.URLField(null=True, blank=True)

    def __unicode__(self):
        self.rainfall_time_step

    @classmethod
    def create(cls, **kwargs):
        if not 'warm_up_period' in kwargs:
            raise ValidationError("ModelInput warm-upPeriod is missing.")
        if not 'rainfall_time_step' in kwargs:
            raise ValidationError("ModelInput rainfallTimeStep is missing.")
        if not 'routing_time_step' in kwargs:
            raise ValidationError("ModelInput routingTimeStep is missing.")
        if not 'simulation_time_step' in kwargs:
            raise ValidationError("ModelInput simulationTimeStep is missing.")
        if not 'watershed_area' in kwargs:
            raise ValidationError("ModelInput watershedArea is missing.")
        if not 'number_of_subbasins' in kwargs:
            raise ValidationError("ModelInput numberOfSubbasins is missing.")
        if not 'number_of_HRUs' in kwargs:
            raise ValidationError("ModelInput numberOfHRUs is missing.")
        if not 'DEM_resolution' in kwargs:
            raise ValidationError("ModelInput DEMresolution is missing.")
        if not 'DEM_source_name' in kwargs:
            raise ValidationError("ModelInput DEMsourceName is missing.")
        if not 'DEM_source_URL' in kwargs:
            raise ValidationError("ModelInput DEMsourceURL is missing.")
        if not 'landUse_data_source_name' in kwargs:
            raise ValidationError("ModelInput landUseDataSourceName is missing.")
        if not 'landUse_data_source_URL' in kwargs:
            raise ValidationError("ModelInput landUseDataSourceURL is missing.")
        if not 'soil_data_source_name' in kwargs:
            raise ValidationError("ModelInput soilDataSourceName is missing.")
        if not 'soil_data_source_URL' in kwargs:
            raise ValidationError("ModelInput soilDataSourceURL is missing.")
        metadata_obj = kwargs['content_object']
        return ModelInput.objects.create(warm_up_period=kwargs['warm_up_period'],
                                             rainfall_time_step=kwargs['rainfall_time_step'],
                                             routing_time_step=kwargs['routing_time_step'],
                                             simulation_time_step=kwargs['simulation_time_step'],
                                             watershed_area=kwargs['watershed_area'],
                                             number_of_subbasins=kwargs['number_of_subbasins'],
                                             number_of_HRUs=kwargs['number_of_HRUs'],
                                             DEM_resolution=kwargs['DEM_resolution'],
                                             DEM_source_name=kwargs['DEM_source_name'],
                                             DEM_source_URL=kwargs['DEM_source_URL'],
                                             landUse_data_source_name=kwargs['landUse_data_source_name'],
                                             landUse_data_source_URL=kwargs['landUse_data_source_URL'],
                                             soil_data_source_name=kwargs['soil_data_source_name'],
                                             soil_data_source_URL=kwargs['soil_data_source_URL'],
                                             content_object=metadata_obj)

    @classmethod
    def update(cls, element_id, **kwargs):
        model_input = ModelInput.objects.get(id=element_id)
        if model_input:
            for key, value in kwargs.iteritems():
                if key in ('warm_up_period', 'rainfall_time_step', 'routing_time_step', 'simulation_time_step', 'watershed_area','number_of_subbasins',
                           'number_of_HRUs', 'DEM_resolution', 'DEM_source_name', 'DEM_source_URL',
                           'landUse_data_source_name', 'landUse_data_source_URL', 'soil_data_source_name', 'soil_data_source_URL'):
                    setattr(model_input, key, value)
            model_input.save()
        else:
            raise ObjectDoesNotExist("No ModelInput element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ModelInput element of a resource can't be deleted.")

#SWAT Model Instance Resource type
class SWATModelInstanceResource(Page, AbstractResource):

    class Meta:
        verbose_name = 'SWAT Model Instance Resource'


    @property
    def metadata(self):
        md = SWATModelInstanceMetaData()
        return self._get_metadata(md)

    @classmethod
    def get_supported_upload_file_types(cls):
        # all file types are supported
        return ('.*',)

    @classmethod
    def can_have_multiple_files(cls):
        return True

    def can_add(self, request):
        return AbstractResource.can_add(self, request)

    def can_change(self, request):
        return AbstractResource.can_change(self, request)

    def can_delete(self, request):
        return AbstractResource.can_delete(self, request)

    def can_view(self, request):
        return AbstractResource.can_view(self, request)

processor_for(SWATModelInstanceResource)(resource_processor)

# metadata container class
class SWATModelInstanceMetaData(CoreMetaData):
    _model_output = generic.GenericRelation(ModelOutput)
    _executed_by = generic.GenericRelation(ExecutedBy)
    _model_objective = generic.GenericRelation(ModelObjective)
    _simulation_type = generic.GenericRelation(simulationType)
    _model_methods = generic.GenericRelation(ModelMethods)
    _swat_model_parameters = generic.GenericRelation(SWATModelParameters)
    _model_input = generic.GenericRelation(ModelInput)

    @property
    def model_output(self):
        return self._model_output.all().first()

    @property
    def executed_by(self):
        return self._executed_by.all().first()

    @property
    def model_objective(self):
        return self._model_objective.all().first()

    @property
    def simulation_type(self):
        return self._simulation_type.all().first()

    @property
    def model_methods(self):
        return self._model_methods.all().first()

    @property
    def swat_model_parameters(self):
        return self._swat_model_parameters.all().first()

    @property
    def model_input(self):
        return self._model_input.all().first()


    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(SWATModelInstanceMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('ModelOutput')
        elements.append('ExecutedBy')
        elements.append('ModelObjective')
        elements.append('simulationType')
        elements.append('ModelMethods')
        elements.append('SWATModelParameters')
        elements.append('ModelInput')
        return elements

    def has_all_required_elements(self):
        if not super(SWATModelInstanceMetaData, self).has_all_required_elements():
            return False
        if not self.model_output:
            return False
        if not self.executed_by:
            return False
        if not self.model_objective:
            return False
        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(SWATModelInstanceMetaData, self).get_required_missing_elements()
        if not self.model_output:
            missing_required_elements.append('ModelOutput')
        if not self.executed_by:
            missing_required_elements.append('ExecutedBy')
        if not self.model_objective:
            missing_required_elements.append('ModelObjective')
        return missing_required_elements


    def get_xml(self, pretty_print=True):
        # get the xml string representation of the core metadata elements
        xml_string = super(SWATModelInstanceMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.model_output:
            hsterms_model_output = etree.SubElement(container, '{%s}ModelOutput' % self.NAMESPACES['hsterms'])
            hsterms_model_output_rdf_Description = etree.SubElement(hsterms_model_output, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_model_output_value = etree.SubElement(hsterms_model_output_rdf_Description, '{%s}IncludesModelOutput' % self.NAMESPACES['hsterms'])
            if self.model_output.includes_output == True: hsterms_model_output_value.text = "Yes"
            else: hsterms_model_output_value.text = "No"
        if self.executed_by:
            hsterms_executed_by = etree.SubElement(container, '{%s}ExecutedBy' % self.NAMESPACES['hsterms'])
            hsterms_executed_by_rdf_Description = etree.SubElement(hsterms_executed_by, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_executed_by_name = etree.SubElement(hsterms_executed_by_rdf_Description, '{%s}ModelProgramName' % self.NAMESPACES['hsterms'])
            hsterms_executed_by_name.text = self.executed_by.name
        if self.model_objective:
            hsterms_model_objective = etree.SubElement(container, '{%s}ModelObjective' % self.NAMESPACES['hsterms'])
            hsterms_model_objective_rdf_Description = etree.SubElement(hsterms_model_objective, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_model_objective_swat_model_objective = etree.SubElement(hsterms_model_objective_rdf_Description, '{%s}ModelObjective' % self.NAMESPACES['hsterms'])
            #hsterms_model_objective_swat_model_objective.text = self.model_objective.swat_model_objective.replace('[', '').replace(']', '').replace("u'", '').replace("',", ',').replace("'", '')
            hsterms_model_objective_swat_model_objective.text = ', '.join([objective.description for objective in self.model_objective.swat_model_objectives.all()])
            hsterms_model_objective_other_objectives = etree.SubElement(hsterms_model_objective_rdf_Description, '{%s}otherObjectives' % self.NAMESPACES['hsterms'])
            hsterms_model_objective_other_objectives.text = self.model_objective.other_objectives
        if self.simulation_type:
            hsterms_simulation_type = etree.SubElement(container, '{%s}simulationType' % self.NAMESPACES['hsterms'])
            hsterms_simulation_type_rdf_Description = etree.SubElement(hsterms_simulation_type, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_simulation_type_name = etree.SubElement(hsterms_simulation_type_rdf_Description, '{%s}simulationType' % self.NAMESPACES['hsterms'])
            hsterms_simulation_type_name.text = self.simulation_type.simulation_type_name
        if self.model_methods:
            hsterms_model_methods = etree.SubElement(container, '{%s}ModelMethods' % self.NAMESPACES['hsterms'])
            hsterms_model_methods_rdf_Description = etree.SubElement(hsterms_model_methods, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_model_methods_runoff_calculation_method = etree.SubElement(hsterms_model_methods_rdf_Description, '{%s}runoffCalculationMethod' % self.NAMESPACES['hsterms'])
            hsterms_model_methods_runoff_calculation_method.text = self.model_methods.runoff_calculation_method
            hsterms_model_methods_flow_routing_method = etree.SubElement(hsterms_model_methods_rdf_Description, '{%s}flowRoutingMethod' % self.NAMESPACES['hsterms'])
            hsterms_model_methods_flow_routing_method.text = self.model_methods.flow_routing_method
            hsterms_model_methods_PET_estimation_method = etree.SubElement(hsterms_model_methods_rdf_Description, '{%s}PETEstimationMethod' % self.NAMESPACES['hsterms'])
            hsterms_model_methods_PET_estimation_method.text = self.model_methods.PET_estimation_method
        if self.swat_model_parameters:
            hsterms_swat_model_parameters = etree.SubElement(container, '{%s}SWATModelParameters' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_rdf_Description = etree.SubElement(hsterms_swat_model_parameters, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_swat_model_parameters_model_parameters = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}ModelParameters' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_model_parameters.text = ', '.join([parameter.description for parameter in self.swat_model_parameters.model_parameters.all()])
            hsterms_swat_model_parameters_other_parameters = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}otherParameters' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_other_parameters.text = self.swat_model_parameters.other_parameters
        if self.model_input:
            hsterms_model_input = etree.SubElement(container, '{%s}ModelInput' % self.NAMESPACES['hsterms'])
            hsterms_model_input_rdf_Description = etree.SubElement(hsterms_model_input, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_model_input_warm_up_period = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}warm-upPeriod' % self.NAMESPACES['hsterms'])
            hsterms_model_input_warm_up_period.text = self.model_input.warm_up_period
            hsterms_model_input_rainfall_time_step = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}rainfallTimeStep' % self.NAMESPACES['hsterms'])
            hsterms_model_input_rainfall_time_step.text = self.model_input.rainfall_time_step
            hsterms_model_input_routing_time_step = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}routingTimeStep' % self.NAMESPACES['hsterms'])
            hsterms_model_input_routing_time_step.text = self.model_input.routing_time_step
            hsterms_model_input_simulation_time_step = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}simulationTimeStep' % self.NAMESPACES['hsterms'])
            hsterms_model_input_simulation_time_step.text = self.model_input.simulation_time_step
            hsterms_model_input_watershed_area = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}watershedArea' % self.NAMESPACES['hsterms'])
            hsterms_model_input_watershed_area.text = self.model_input.watershed_area+ ' km2'
            hsterms_model_input_number_of_subbasins = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}numberOfSubbasins' % self.NAMESPACES['hsterms'])
            hsterms_model_input_number_of_subbasins.text = self.model_input.number_of_subbasins
            hsterms_model_input_number_of_HRUs = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}numberOfHRUs' % self.NAMESPACES['hsterms'])
            hsterms_model_input_number_of_HRUs.text = self.model_input.number_of_HRUs
            hsterms_model_input_DEM_resolution = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}DEMResolution' % self.NAMESPACES['hsterms'])
            hsterms_model_input_DEM_resolution.text = self.model_input.DEM_resolution + ' m'
            hsterms_model_input_DEM_source_name = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}DEMSourceName' % self.NAMESPACES['hsterms'])
            hsterms_model_input_DEM_source_name.text = self.model_input.DEM_source_name
            hsterms_model_input_DEM_source_URL = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}DEMSourceURL' % self.NAMESPACES['hsterms'])
            hsterms_model_input_DEM_source_URL.text = self.model_input.DEM_source_URL
            hsterms_model_input_landUse_data_source_name = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}landUseDataSourceName' % self.NAMESPACES['hsterms'])
            hsterms_model_input_landUse_data_source_name.text = self.model_input.landUse_data_source_name
            hsterms_model_input_landUse_data_source_URL = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}landUseDataSourceURL' % self.NAMESPACES['hsterms'])
            hsterms_model_input_landUse_data_source_URL.text = self.model_input.landUse_data_source_URL
            hsterms_model_input_soil_data_source_name = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}soilDataSourceName' % self.NAMESPACES['hsterms'])
            hsterms_model_input_soil_data_source_name.text = self.model_input.soil_data_source_name
            hsterms_model_input_soil_data_source_URL = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}soilDataSourceURL' % self.NAMESPACES['hsterms'])
            hsterms_model_input_soil_data_source_URL.text = self.model_input.soil_data_source_URL

        return etree.tostring(RDF_ROOT, pretty_print=True)

import receivers