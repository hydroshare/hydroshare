__author__ = 'Mohamed Morsy'
from lxml import etree

from django.contrib.contenttypes import generic
from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, AbstractMetaDataElement
from hs_core.hydroshare import utils

from hs_model_program.models import ModelProgramResource

# extended metadata elements for SWAT Model Instance resource type
class ModelOutput(AbstractMetaDataElement):
    term = 'ModelOutput'
    includes_output = models.BooleanField(default=False)

class ExecutedBy(AbstractMetaDataElement):
    term = 'ExecutedBY'
    model_name = models.CharField(max_length=500, choices=(('-', '    '),), default=None)
    model_program_fk = models.ForeignKey('hs_model_program.ModelProgramResource', null=True, blank=True,related_name='swatmodelinstance')

    def __unicode__(self):
        self.model_name

    @classmethod
    def create(cls, **kwargs):
        shortid = kwargs['model_name']
        # get the MP object that matches.  Returns None if nothing is found
        obj = ModelProgramResource.objects.filter(short_id=shortid).first()
        metadata_obj = kwargs['content_object']
        title = obj.title
        return super(ExecutedBy,cls).create(model_program_fk=obj, model_name=title,content_object=metadata_obj)

    @classmethod
    def update(cls, element_id, **kwargs):
        shortid = kwargs['model_name']
        # get the MP object that matches.  Returns None if nothing is found
        obj = ModelProgramResource.objects.filter(short_id=shortid).first()
        return super(ExecutedBy,cls).update(model_program_fk=obj, element_id=element_id)

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
        metadata_obj = kwargs['content_object']
        model_objective = super(ModelObjective,cls).create(other_objectives=kwargs['other_objectives'],content_object=metadata_obj)
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
    def _validate_swat_model_objectives(cls, objectives):
        for swat_objective in objectives:
            if swat_objective not in ['Hydrology', 'Water quality', 'BMPs', 'Climate / Landuse Change']:
                raise ValidationError('Invalid swat_model_objectives:%s' % objectives)

class SimulationType(AbstractMetaDataElement):
    term = 'SimulationType'
    type_choices = (('Normal Simulation', 'Normal Simulation'), ('Sensitivity Analysis', 'Sensitivity Analysis'),
                    ('Auto-Calibration', 'Auto-Calibration'))
    simulation_type_name = models.CharField(max_length=100, choices=type_choices, verbose_name='Simulation type')

    def __unicode__(self):
        self.simulation_type_name

class ModelMethod(AbstractMetaDataElement):
    term = 'ModelMethod'
    runoff_calculation_method = models.CharField(max_length=200, null=True, blank=True)
    flow_routing_method = models.CharField(max_length=200, null=True, blank=True)
    PET_estimation_method = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        self.runoff_calculation_method

class ModelParametersChoices(models.Model):
    description = models.CharField(max_length=300)

    def __unicode__(self):
        self.description

class ModelParameter(AbstractMetaDataElement):
    term = 'ModelParameter'
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
        metadata_obj = kwargs['content_object']
        swat_model_parameters = super(ModelParameter,cls).create(other_parameters=kwargs['other_parameters'],content_object=metadata_obj)
        for swat_parameter in kwargs['model_parameters']:
            qs = ModelParametersChoices.objects.filter(description__iexact=swat_parameter)
            if qs.exists():
                swat_model_parameters.model_parameters.add(qs[0])
            else:
                swat_model_parameters.model_parameters.create(description=swat_parameter)

        return swat_model_parameters

    @classmethod
    def update(cls, element_id, **kwargs):
        swat_model_parameters = ModelParameter.objects.get(id=element_id)
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
            raise ObjectDoesNotExist("No ModelParameter element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def _validate_swat_model_parameters(cls, parameters):
        for swat_parameters in parameters:
            if swat_parameters not in ['Crop rotation', 'Tile drainage', 'Point source', 'Fertilizer', 'Tillage operation', 'Inlet of draining watershed', 'Irrigation operation']:
                raise ValidationError('Invalid swat_model_parameters:%s' % parameters)

class ModelInput(AbstractMetaDataElement):
    term = 'ModelInput'
    rainfall_type_choices = (('Daily', 'Daily'), ('Sub-hourly', 'Sub-hourly'),)
    routing_type_choices = (('Daily', 'Daily'), ('Hourly', 'Hourly'),)
    simulation_type_choices = (('Annual', 'Annual'), ('Monthly', 'Monthly'), ('Daily', 'Daily'), ('Hourly', 'Hourly'),)

    warm_up_period = models.CharField(max_length=100, null=True, blank=True, verbose_name='Warm-up period in years')
    rainfall_time_step_type = models.CharField(max_length=100, choices=rainfall_type_choices, null=True, blank=True)
    rainfall_time_step_value = models.CharField(max_length=100, null=True, blank=True)
    routing_time_step_type = models.CharField(max_length=100, choices=routing_type_choices, null=True, blank=True)
    routing_time_step_value = models.CharField(max_length=100, null=True, blank=True)
    simulation_time_step_type = models.CharField(max_length=100,choices=simulation_type_choices, null=True, blank=True)
    simulation_time_step_value = models.CharField(max_length=100, null=True, blank=True)
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

#SWAT Model Instance Resource type
class SWATModelInstanceResource(BaseResource):
    objects = ResourceManager("SWATModelInstanceResource")

    class Meta:
        verbose_name = 'SWAT Model Instance Resource'
        proxy = True

    @property
    def metadata(self):
        md = SWATModelInstanceMetaData()
        return self._get_metadata(md)

    @classmethod
    def get_supported_upload_file_types(cls):
        # all file types are supported
        return ('.*')

    @classmethod
    def can_have_multiple_files(cls):
        return True

processor_for(SWATModelInstanceResource)(resource_processor)

# metadata container class
class SWATModelInstanceMetaData(CoreMetaData):
    _model_output = generic.GenericRelation(ModelOutput)
    _executed_by = generic.GenericRelation(ExecutedBy)
    _model_objective = generic.GenericRelation(ModelObjective)
    _simulation_type = generic.GenericRelation(SimulationType)
    _model_method = generic.GenericRelation(ModelMethod)
    _model_parameter = generic.GenericRelation(ModelParameter)
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
    def model_method(self):
        return self._model_method.all().first()

    @property
    def model_parameter(self):
        return self._model_parameter.all().first()

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
        elements.append('SimulationType')
        elements.append('ModelMethod')
        elements.append('ModelParameter')
        elements.append('ModelInput')
        return elements

    def has_all_required_elements(self):
        if not super(SWATModelInstanceMetaData, self).has_all_required_elements():
            return False
        if not self.model_objective:
            return False
        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(SWATModelInstanceMetaData, self).get_required_missing_elements()
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
            hsterms_model_output_value = etree.SubElement(hsterms_model_output_rdf_Description, '{%s}includesModelOutput' % self.NAMESPACES['hsterms'])
        if self.model_output.includes_output == True:
            hsterms_model_output_value.text = "Yes"
        else:
            hsterms_model_output_value.text = "No"

        hsterms_executed_by = etree.SubElement(container, '{%s}ExecutedBy' % self.NAMESPACES['hsterms'])
        hsterms_executed_by_rdf_Description = etree.SubElement(hsterms_executed_by, '{%s}Description' % self.NAMESPACES['rdf'])
        hsterms_executed_by_name = etree.SubElement(hsterms_executed_by_rdf_Description, '{%s}modelProgramName' % self.NAMESPACES['hsterms'])
        hsterms_executed_by_url = etree.SubElement(hsterms_executed_by_rdf_Description, '{%s}modelProgramIdentifier' % self.NAMESPACES['hsterms'])
        if self.executed_by:
            title = self.executed_by.model_program_fk.title
            url = '%s%s' % (utils.current_site_url(), self.executed_by.model_program_fk.get_absolute_url())
        else:
            title = "Unspecified"
            url = "None"
        hsterms_executed_by_url.text = url
        hsterms_executed_by_name.text = title

        if self.model_objective:
            hsterms_model_objective = etree.SubElement(container, '{%s}modelObjective' % self.NAMESPACES['hsterms'])

            if self.model_objective.other_objectives:
                hsterms_model_objective.text = ', '.join([objective.description for objective in self.model_objective.swat_model_objectives.all()]) + ', ' + self.model_objective.other_objectives
            else:
                hsterms_model_objective.text = ', '.join([objective.description for objective in self.model_objective.swat_model_objectives.all()])


        if self.simulation_type:
            hsterms_simulation_type = etree.SubElement(container, '{%s}simulationType' % self.NAMESPACES['hsterms'])
            hsterms_simulation_type.text = self.simulation_type.simulation_type_name


        if self.model_method:
            hsterms_model_methods = etree.SubElement(container, '{%s}ModelMethod' % self.NAMESPACES['hsterms'])
            hsterms_model_methods_rdf_Description = etree.SubElement(hsterms_model_methods, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_model_methods_runoff_calculation_method = etree.SubElement(hsterms_model_methods_rdf_Description, '{%s}runoffCalculationMethod' % self.NAMESPACES['hsterms'])
            hsterms_model_methods_runoff_calculation_method.text = self.model_method.runoff_calculation_method
            hsterms_model_methods_flow_routing_method = etree.SubElement(hsterms_model_methods_rdf_Description, '{%s}flowRoutingMethod' % self.NAMESPACES['hsterms'])
            hsterms_model_methods_flow_routing_method.text = self.model_method.flow_routing_method
            hsterms_model_methods_PET_estimation_method = etree.SubElement(hsterms_model_methods_rdf_Description, '{%s}petEstimationMethod' % self.NAMESPACES['hsterms'])
            hsterms_model_methods_PET_estimation_method.text = self.model_method.PET_estimation_method


        if self.model_parameter:
            hsterms_swat_model_parameters = etree.SubElement(container, '{%s}modelParameter' % self.NAMESPACES['hsterms'])

            if self.model_parameter.other_parameters:
                hsterms_swat_model_parameters.text = ', '.join([parameter.description for parameter in self.model_parameter.model_parameters.all()]) + ', ' + self.model_parameter.other_parameters
            else:
                hsterms_swat_model_parameters.text = ', '.join([parameter.description for parameter in self.model_parameter.model_parameters.all()])


        if self.model_input:
            hsterms_model_input = etree.SubElement(container, '{%s}ModelInput' % self.NAMESPACES['hsterms'])
            hsterms_model_input_rdf_Description = etree.SubElement(hsterms_model_input, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_model_input_warm_up_period_type = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}warm-upPeriodType' % self.NAMESPACES['hsterms'])
            hsterms_model_input_warm_up_period_type.text = 'Year'
            hsterms_model_input_warm_up_period_value = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}warm-upPeriodValue' % self.NAMESPACES['hsterms'])
            hsterms_model_input_warm_up_period_value.text = self.model_input.warm_up_period
            hsterms_model_input_rainfall_time_step_type = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}rainfallTimeStepType' % self.NAMESPACES['hsterms'])
            hsterms_model_input_rainfall_time_step_type.text = self.model_input.rainfall_time_step_type
            hsterms_model_input_rainfall_time_step_value = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}rainfallTimeStepValue' % self.NAMESPACES['hsterms'])
            hsterms_model_input_rainfall_time_step_value.text = self.model_input.rainfall_time_step_value
            hsterms_model_input_routing_time_step_type = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}routingTimeStepType' % self.NAMESPACES['hsterms'])
            hsterms_model_input_routing_time_step_type.text = self.model_input.routing_time_step_type
            hsterms_model_input_routing_time_step_value = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}routingTimeStepValue' % self.NAMESPACES['hsterms'])
            hsterms_model_input_routing_time_step_value.text = self.model_input.routing_time_step_value
            hsterms_model_input_simulation_time_step_type = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}simulationTimeStepType' % self.NAMESPACES['hsterms'])
            hsterms_model_input_simulation_time_step_type.text = self.model_input.simulation_time_step_type
            hsterms_model_input_simulation_time_step_value = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}simulationTimeStepValue' % self.NAMESPACES['hsterms'])
            hsterms_model_input_simulation_time_step_value.text = self.model_input.simulation_time_step_value
            hsterms_model_input_watershed_area = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}watershedArea' % self.NAMESPACES['hsterms'])
            hsterms_model_input_watershed_area.text = self.model_input.watershed_area
            hsterms_model_input_number_of_subbasins = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}numberOfSubbasins' % self.NAMESPACES['hsterms'])
            hsterms_model_input_number_of_subbasins.text = self.model_input.number_of_subbasins
            hsterms_model_input_number_of_HRUs = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}numberOfHRUs' % self.NAMESPACES['hsterms'])
            hsterms_model_input_number_of_HRUs.text = self.model_input.number_of_HRUs
            hsterms_model_input_DEM_resolution = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}demResolution' % self.NAMESPACES['hsterms'])
            hsterms_model_input_DEM_resolution.text = self.model_input.DEM_resolution
            hsterms_model_input_DEM_source_name = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}demSourceName' % self.NAMESPACES['hsterms'])
            hsterms_model_input_DEM_source_name.text = self.model_input.DEM_source_name
            hsterms_model_input_DEM_source_URL = etree.SubElement(hsterms_model_input_rdf_Description, '{%s}demSourceURL' % self.NAMESPACES['hsterms'])
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

    def delete_all_elements(self):
        super(SWATModelInstanceMetaData, self).delete_all_elements()
        self._model_output.all().delete()
        self._executed_by.all().delete()
        self._model_objective.all().delete()
        self._simulation_type.all().delete()
        self._model_method.all().delete()
        self._model_parameter.all().delete()
        self._model_input.all().delete()

import receivers