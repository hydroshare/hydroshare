__author__ = 'Mohamed Morsy'
from lxml import etree

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, AbstractMetaDataElement
from hs_core.hydroshare import utils

from hs_model_program.models import ModelProgramResource
from hs_modelinstance.models import ModelInstanceMetaData, ModelOutput, ExecutedBy

class ModelOutput(ModelOutput):
    class Meta:
        proxy = True

class ExecutedBy(ExecutedBy):
    class Meta:
        proxy = True

# extended metadata elements for SWAT Model Instance resource type
class ModelObjectiveChoices(models.Model):
    description = models.CharField(max_length=300)

    def __unicode__(self):
        return self.description

class ModelObjective(AbstractMetaDataElement):
    term = 'ModelObjective'
    swat_model_objectives = models.ManyToManyField(ModelObjectiveChoices, null=True, blank=True)
    other_objectives = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        return self.other_objectives
    
    class Meta:
        # ModelObjective element is not repeatable
        unique_together = ("content_type", "object_id")

    def get_swat_model_objectives(self):
        return ', '.join([objective.description for objective in self.swat_model_objectives.all()])

    @classmethod
    def _add_swat_objective(cls,model_objective,objectives):
        for swat_objective in objectives:
            qs = ModelObjectiveChoices.objects.filter(description__iexact=swat_objective)
            if qs.exists():
                model_objective.swat_model_objectives.add(qs[0])
            else:
                model_objective.swat_model_objectives.create(description=swat_objective)

    @classmethod
    def create(cls, **kwargs):
        if 'swat_model_objectives' in kwargs:
            cls._validate_swat_model_objectives(kwargs['swat_model_objectives'])
        else:
            raise ValidationError("swat_model_objectives is missing.")
        model_objective = super(ModelObjective,cls).create(content_object=kwargs['content_object'], other_objectives=kwargs['other_objectives'])
        cls._add_swat_objective(model_objective, kwargs['swat_model_objectives'])

        return model_objective

    @classmethod
    def update(cls, element_id, **kwargs):
        model_objective = ModelObjective.objects.get(id=element_id)
        if model_objective:
            if 'swat_model_objectives' in kwargs:
                cls._validate_swat_model_objectives(kwargs['swat_model_objectives'])
                # delete the the m2m association records
                model_objective.swat_model_objectives.clear()
                cls._add_swat_objective(model_objective, kwargs['swat_model_objectives'])

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
        return self.simulation_type_name

    class Meta:
        # SimulationType element is not repeatable
        unique_together = ("content_type", "object_id")

class ModelMethod(AbstractMetaDataElement):
    term = 'ModelMethod'
    runoffCalculationMethod = models.CharField(max_length=200, null=True, blank=True, verbose_name='Runoff calculation method')
    flowRoutingMethod = models.CharField(max_length=200, null=True, blank=True, verbose_name='Flow routing method')
    petEstimationMethod = models.CharField(max_length=200, null=True, blank=True, verbose_name='PET estimation method')

    def __unicode__(self):
        return self.runoffCalculationMethod

    class Meta:
        # ModelMethod element is not repeatable
        unique_together = ("content_type", "object_id")

class ModelParametersChoices(models.Model):
    description = models.CharField(max_length=300)

    def __unicode__(self):
        return self.description

class ModelParameter(AbstractMetaDataElement):
    term = 'ModelParameter'
    model_parameters = models.ManyToManyField(ModelParametersChoices, null=True, blank=True)
    other_parameters = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        return self.other_parameters

    class Meta:
        # ModelParameter element is not repeatable
        unique_together = ("content_type", "object_id")

    def get_swat_model_parameters(self):
        return ', '.join([parameter.description for parameter in self.model_parameters.all()])

    @classmethod
    def _add_swat_parameters(cls,swat_model_parameters,parameters):
        for swat_parameter in parameters:
            qs = ModelParametersChoices.objects.filter(description__iexact=swat_parameter)
            if qs.exists():
                swat_model_parameters.model_parameters.add(qs[0])
            else:
                swat_model_parameters.model_parameters.create(description=swat_parameter)

    @classmethod
    def create(cls, **kwargs):
        if 'model_parameters' in kwargs:
            cls._validate_swat_model_parameters(kwargs['model_parameters'])
        else:
            raise ValidationError("model_parameters is missing.")
        swat_model_parameters = super(ModelParameter,cls).create(content_object=kwargs['content_object'], other_parameters=kwargs['other_parameters'])
        cls._add_swat_parameters(swat_model_parameters,kwargs['model_parameters'])

        return swat_model_parameters

    @classmethod
    def update(cls, element_id, **kwargs):
        swat_model_parameters = ModelParameter.objects.get(id=element_id)
        if swat_model_parameters:
            if 'model_parameters' in kwargs:
                cls._validate_swat_model_parameters(kwargs['model_parameters'])
                # delete the the m2m association records
                swat_model_parameters.model_parameters.clear()
                cls._add_swat_parameters(swat_model_parameters,kwargs['model_parameters'])

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

    warmupPeriodValue = models.CharField(max_length=100, null=True, blank=True, verbose_name='Warm-up period in years')
    rainfallTimeStepType = models.CharField(max_length=100, choices=rainfall_type_choices, null=True, blank=True, verbose_name='Rainfall time step type')
    rainfallTimeStepValue = models.CharField(max_length=100, null=True, blank=True, verbose_name='Rainfall time step value')
    routingTimeStepType = models.CharField(max_length=100, choices=routing_type_choices, null=True, blank=True, verbose_name='Routing time step type')
    routingTimeStepValue = models.CharField(max_length=100, null=True, blank=True, verbose_name='Routing time step value')
    simulationTimeStepType = models.CharField(max_length=100,choices=simulation_type_choices, null=True, blank=True, verbose_name='Simulation time step type')
    simulationTimeStepValue = models.CharField(max_length=100, null=True, blank=True, verbose_name='Simulation time step value')
    watershedArea = models.CharField(max_length=100, null=True, blank=True, verbose_name='Watershed area in square kilometers')
    numberOfSubbasins = models.CharField(max_length=100, null=True, blank=True, verbose_name='Number of subbasins')
    numberOfHRUs = models.CharField(max_length=100, null=True, blank=True, verbose_name='Number of HRUs')
    demResolution = models.CharField(max_length=100, null=True, blank=True, verbose_name='DEM resolution in meters')
    demSourceName = models.CharField(max_length=200, null=True, blank=True, verbose_name='DEM source name')
    demSourceURL = models.URLField(null=True, blank=True, verbose_name='DEM source URL')
    landUseDataSourceName = models.CharField(max_length=200, null=True, blank=True, verbose_name='LandUse data source name')
    landUseDataSourceURL = models.URLField(null=True, blank=True, verbose_name='LandUse data source URL')
    soilDataSourceName = models.CharField(max_length=200, null=True, blank=True, verbose_name='Soil data source name')
    soilDataSourceURL = models.URLField(null=True, blank=True, verbose_name='Soil data source URL')

    def __unicode__(self):
        return self.warmupPeriodType

    class Meta:
        # ModelInput element is not repeatable
        unique_together = ("content_type", "object_id")

    @property
    def warmupPeriodType(self):
        return "Year"

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
class SWATModelInstanceMetaData(ModelInstanceMetaData):
    _model_objective = GenericRelation(ModelObjective)
    _simulation_type = GenericRelation(SimulationType)
    _model_method = GenericRelation(ModelMethod)
    _model_parameter = GenericRelation(ModelParameter)
    _model_input = GenericRelation(ModelInput)

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
            modelMethodFields = ['runoffCalculationMethod','flowRoutingMethod','petEstimationMethod']
            self.add_metadata_element_to_xml(container,self.model_method,modelMethodFields)

        if self.model_parameter:
            hsterms_swat_model_parameters = etree.SubElement(container, '{%s}modelParameter' % self.NAMESPACES['hsterms'])

            if self.model_parameter.other_parameters:
                hsterms_swat_model_parameters.text = ', '.join([parameter.description for parameter in self.model_parameter.model_parameters.all()]) + ', ' + self.model_parameter.other_parameters
            else:
                hsterms_swat_model_parameters.text = ', '.join([parameter.description for parameter in self.model_parameter.model_parameters.all()])


        if self.model_input:
            modelInputFields = ['warmupPeriodType','warmupPeriodValue','rainfallTimeStepType','rainfallTimeStepValue','routingTimeStepType',\
                                'routingTimeStepValue','simulationTimeStepType','simulationTimeStepValue','watershedArea','numberOfSubbasins',\
                                'numberOfHRUs','demResolution','demSourceName','demSourceURL','landUseDataSourceName','landUseDataSourceURL',\
                                'soilDataSourceName','soilDataSourceURL']
            self.add_metadata_element_to_xml(container,self.model_input,modelInputFields)

        return etree.tostring(RDF_ROOT, pretty_print=True)

    def delete_all_elements(self):
        super(SWATModelInstanceMetaData, self).delete_all_elements()
        self._model_objective.all().delete()
        self._simulation_type.all().delete()
        self._model_method.all().delete()
        self._model_parameter.all().delete()
        self._model_input.all().delete()

import receivers