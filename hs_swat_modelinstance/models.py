from lxml import etree

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, \
    AbstractMetaDataElement
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
    swat_model_objectives = models.ManyToManyField(ModelObjectiveChoices, blank=True)
    other_objectives = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        return self.other_objectives

    class Meta:
        # ModelObjective element is not repeatable
        unique_together = ("content_type", "object_id")

    def get_swat_model_objectives(self):
        return ', '.join([objective.description for objective in self.swat_model_objectives.all()])

    @classmethod
    def _add_swat_objective(cls, model_objective, objectives):
        """ there are two possibilities for swat_objective values: list of string (during normal
         create or update) or integer (during creating new version of the resource)"""
        for swat_objective in objectives:
            if isinstance(swat_objective, int):
                qs = ModelObjectiveChoices.objects.filter(id=swat_objective)
            else:
                qs = ModelObjectiveChoices.objects.filter(description__iexact=swat_objective)
            if qs.exists():
                model_objective.swat_model_objectives.add(qs[0])
            else:
                if isinstance(swat_objective, basestring):
                    model_objective.swat_model_objectives.create(description=swat_objective)

    @classmethod
    def create(cls, **kwargs):
        if 'swat_model_objectives' in kwargs:
            cls._validate_swat_model_objectives(kwargs['swat_model_objectives'])
        else:
            raise ValidationError("swat_model_objectives is missing.")
        model_objective = super(ModelObjective, cls).create(
            content_object=kwargs['content_object'],
            other_objectives=kwargs['other_objectives'])
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
            if len(model_objective.swat_model_objectives.all()) == 0 and \
                    len(model_objective.other_objectives) == 0:
                model_objective.delete()
        else:
            raise ObjectDoesNotExist("No ModelObjective element was found for the provided id:%s"
                                     % kwargs['id'])

    @classmethod
    def _validate_swat_model_objectives(cls, objectives):
        for swat_objective in objectives:
            if isinstance(swat_objective, basestring) and swat_objective not in [
                'Hydrology',
                'Water quality',
                'BMPs',
                'Climate / Landuse Change'
            ]:
                raise ValidationError('Invalid swat_model_objectives:%s' % objectives)


class SimulationType(AbstractMetaDataElement):
    term = 'SimulationType'
    type_choices = (('Normal Simulation', 'Normal Simulation'),
                    ('Sensitivity Analysis', 'Sensitivity Analysis'),
                    ('Auto-Calibration', 'Auto-Calibration'))
    simulation_type_name = models.CharField(max_length=100, choices=type_choices,
                                            verbose_name='Simulation type')

    def __unicode__(self):
        return self.simulation_type_name

    class Meta:
        # SimulationType element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        if 'simulation_type_name' in kwargs:
            if kwargs['simulation_type_name'] == 'Choose a type':
                kwargs['simulation_type_name'] = ''
                return super(SimulationType, cls).create(**kwargs)
            cls._validate_simulation_type(kwargs['simulation_type_name'])
        else:
            raise ValidationError("simulation_type_name is missing.")
        simulation_type = super(SimulationType, cls).create(**kwargs)
        return simulation_type

    @classmethod
    def update(cls, element_id, **kwargs):
        if 'simulation_type_name' in kwargs:
            if kwargs['simulation_type_name'] == 'Choose a type':
                kwargs['simulation_type_name'] = ''
                return super(SimulationType, cls).update(element_id, **kwargs)
            cls._validate_simulation_type(kwargs['simulation_type_name'])
        else:
            raise ValidationError("simulation_type_name is missing.")
        simulation_type = super(SimulationType, cls).update(element_id, **kwargs)
        return simulation_type

    @classmethod
    def _validate_simulation_type(cls, swat_simulation_type):
        types = [c[0] for c in cls.type_choices]
        if swat_simulation_type != '' and swat_simulation_type not in types:
            raise ValidationError('Invalid swat_model_simulation_type:{} not in {}'.format(
                swat_simulation_type, types)
            )


class ModelMethod(AbstractMetaDataElement):
    term = 'ModelMethod'
    runoffCalculationMethod = models.CharField(max_length=200, null=True, blank=True,
                                               verbose_name='Runoff calculation method')
    flowRoutingMethod = models.CharField(max_length=200, null=True, blank=True,
                                         verbose_name='Flow routing method')
    petEstimationMethod = models.CharField(max_length=200, null=True, blank=True,
                                           verbose_name='PET estimation method')

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
    model_parameters = models.ManyToManyField(ModelParametersChoices, blank=True)
    other_parameters = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        return self.other_parameters

    class Meta:
        # ModelParameter element is not repeatable
        unique_together = ("content_type", "object_id")

    def get_swat_model_parameters(self):
        return ', '.join([parameter.description for parameter in self.model_parameters.all()])

    @classmethod
    def _add_swat_parameters(cls, swat_model_parameters, parameters):
        """ there are two possibilities for swat_parameter values: list of string (during normal
         create or update) or integer (during creating new version of the resource)"""
        for swat_parameter in parameters:
            if isinstance(swat_parameter, int):
                qs = ModelParametersChoices.objects.filter(id=swat_parameter)
            else:
                qs = ModelParametersChoices.objects.filter(description__iexact=swat_parameter)
            if qs.exists():
                swat_model_parameters.model_parameters.add(qs[0])
            else:
                if isinstance(swat_parameter, basestring):
                    swat_model_parameters.model_parameters.create(description=swat_parameter)

    @classmethod
    def create(cls, **kwargs):
        if 'model_parameters' in kwargs:
            cls._validate_swat_model_parameters(kwargs['model_parameters'])
        else:
            raise ValidationError("model_parameters is missing.")
        swat_model_parameters = super(ModelParameter, cls).create(
            content_object=kwargs['content_object'],
            other_parameters=kwargs['other_parameters']
        )
        cls._add_swat_parameters(swat_model_parameters, kwargs['model_parameters'])

        return swat_model_parameters

    @classmethod
    def update(cls, element_id, **kwargs):
        swat_model_parameters = ModelParameter.objects.get(id=element_id)
        if swat_model_parameters:
            if 'model_parameters' in kwargs:
                cls._validate_swat_model_parameters(kwargs['model_parameters'])
                # delete the the m2m association records
                swat_model_parameters.model_parameters.clear()
                cls._add_swat_parameters(swat_model_parameters, kwargs['model_parameters'])

            if 'other_parameters' in kwargs:
                swat_model_parameters.other_parameters = kwargs['other_parameters']

            swat_model_parameters.save()

            # delete model_parameters metadata element if it has no data
            if swat_model_parameters.model_parameters.all().count() == 0 and \
                    len(swat_model_parameters.other_parameters) == 0:
                swat_model_parameters.delete()
        else:
            raise ObjectDoesNotExist("No ModelParameter element was found for the provided id:%s"
                                     % kwargs['id'])

    @classmethod
    def _validate_swat_model_parameters(cls, parameters):
        for swat_parameters in parameters:
            if isinstance(swat_parameters, basestring) and swat_parameters not in [
                'Crop rotation',
                'Tile drainage',
                'Point source',
                'Fertilizer',
                'Tillage operation',
                'Inlet of draining watershed',
                'Irrigation operation'
            ]:
                raise ValidationError('Invalid swat_model_parameters:%s' % parameters)


class ModelInput(AbstractMetaDataElement):
    term = 'ModelInput'
    rainfall_type_choices = (('Daily', 'Daily'), ('Sub-hourly', 'Sub-hourly'),)
    routing_type_choices = (('Daily', 'Daily'), ('Hourly', 'Hourly'),)
    simulation_type_choices = (('Annual', 'Annual'), ('Monthly', 'Monthly'), ('Daily', 'Daily'),
                               ('Hourly', 'Hourly'),)

    warmupPeriodValue = models.CharField(max_length=100, null=True, blank=True,
                                         verbose_name='Warm-up period in years')
    rainfallTimeStepType = models.CharField(max_length=100, choices=rainfall_type_choices,
                                            null=True, blank=True,
                                            verbose_name='Rainfall time step type')
    rainfallTimeStepValue = models.CharField(max_length=100, null=True, blank=True,
                                             verbose_name='Rainfall time step value')
    routingTimeStepType = models.CharField(max_length=100, choices=routing_type_choices,
                                           null=True, blank=True,
                                           verbose_name='Routing time step type')
    routingTimeStepValue = models.CharField(max_length=100, null=True, blank=True,
                                            verbose_name='Routing time step value')
    simulationTimeStepType = models.CharField(max_length=100, choices=simulation_type_choices,
                                              null=True, blank=True,
                                              verbose_name='Simulation time step type')
    simulationTimeStepValue = models.CharField(max_length=100, null=True, blank=True,
                                               verbose_name='Simulation time step value')
    watershedArea = models.CharField(max_length=100, null=True, blank=True,
                                     verbose_name='Watershed area in square kilometers')
    numberOfSubbasins = models.CharField(max_length=100, null=True, blank=True,
                                         verbose_name='Number of subbasins')
    numberOfHRUs = models.CharField(max_length=100, null=True, blank=True,
                                    verbose_name='Number of HRUs')
    demResolution = models.CharField(max_length=100, null=True, blank=True,
                                     verbose_name='DEM resolution in meters')
    demSourceName = models.CharField(max_length=200, null=True, blank=True,
                                     verbose_name='DEM source name')
    demSourceURL = models.URLField(null=True, blank=True, verbose_name='DEM source URL')
    landUseDataSourceName = models.CharField(max_length=200, null=True, blank=True,
                                             verbose_name='LandUse data source name')
    landUseDataSourceURL = models.URLField(null=True, blank=True,
                                           verbose_name='LandUse data source URL')
    soilDataSourceName = models.CharField(max_length=200, null=True, blank=True,
                                          verbose_name='Soil data source name')
    soilDataSourceURL = models.URLField(null=True, blank=True, verbose_name='Soil data source URL')

    def __unicode__(self):
        return self.warmupPeriodType

    class Meta:
        # ModelInput element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        kwargs = cls._validate_time_step(**kwargs)
        model_input = super(ModelInput, cls).create(**kwargs)
        return model_input

    @classmethod
    def update(cls, element_id, **kwargs):
        kwargs = cls._validate_time_step(**kwargs)
        model_input = super(ModelInput, cls).update(element_id, **kwargs)
        return model_input

    @property
    def warmupPeriodType(self):
        return "Year"

    @classmethod
    def _validate_time_step(cls, **kwargs):
        for key, val in kwargs.iteritems():
            if val == 'Choose a type':
                kwargs[key] = ''
            elif val != '':
                time_step = val
                if key == 'rainfallTimeStepType':
                    types = [c[0] for c in cls.rainfall_type_choices]
                    cls.check_time_steps(time_step, types)
                elif key == 'routingTimeStepType':
                    types = [c[0] for c in cls.routing_type_choices]
                    cls.check_time_steps(time_step, types)
                elif key == 'simulationTimeStepType':
                    types = [c[0] for c in cls.simulation_type_choices]
                    cls.check_time_steps(time_step, types)
        return kwargs

    @classmethod
    def check_time_steps(cls, time_step, types):
        if time_step not in types:
            raise ValidationError('Invalid time step choice:{} not in {}'.format(time_step, types))


# SWAT Model Instance Resource type
class SWATModelInstanceResource(BaseResource):
    objects = ResourceManager("SWATModelInstanceResource")

    discovery_content_type = 'SWAT Model Instance'  # used during discovery

    class Meta:
        verbose_name = 'SWAT Model Instance Resource'
        proxy = True

    @classmethod
    def get_metadata_class(cls):
        return SWATModelInstanceMetaData

    @classmethod
    def get_supported_upload_file_types(cls):
        # all file types are supported
        return '.*'


processor_for(SWATModelInstanceResource)(resource_processor)


# metadata container class
class SWATModelInstanceMetaData(ModelInstanceMetaData):
    _model_objective = GenericRelation(ModelObjective)
    _simulation_type = GenericRelation(SimulationType)
    _model_method = GenericRelation(ModelMethod)
    _model_parameter = GenericRelation(ModelParameter)
    _model_input = GenericRelation(ModelInput)

    @property
    def resource(self):
        return SWATModelInstanceResource.objects.filter(object_id=self.id).first()

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

    @property
    def serializer(self):
        """Return an instance of rest_framework Serializer for self """
        from serializers import SWATModelInstanceMetaDataSerializer
        return SWATModelInstanceMetaDataSerializer(self)

    @classmethod
    def parse_for_bulk_update(cls, metadata, parsed_metadata):
        """Overriding the base class method"""

        ModelInstanceMetaData.parse_for_bulk_update(metadata, parsed_metadata)
        keys_to_update = metadata.keys()
        if 'modelobjective' in keys_to_update:
            parsed_metadata.append({"modelobjective": metadata.pop('modelobjective')})

        if 'simulationtype' in keys_to_update:
            parsed_metadata.append({"simulationtype": metadata.pop('simulationtype')})

        if 'modelmethod' in keys_to_update:
            parsed_metadata.append({"modelmethod": metadata.pop('modelmethod')})

        if 'modelparameter' in keys_to_update:
            parsed_metadata.append({"modelparameter": metadata.pop('modelparameter')})

        if 'modelinput' in keys_to_update:
            parsed_metadata.append({"modelinput": metadata.pop('modelinput')})

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
        missing_required_elements = \
            super(SWATModelInstanceMetaData, self).get_required_missing_elements()
        if not self.model_objective:
            missing_required_elements.append('ModelObjective')
        return missing_required_elements

    def update(self, metadata, user):
        # overriding the base class update method for bulk update of metadata
        from forms import ModelInputValidationForm, ModelMethodValidationForm, \
            SimulationTypeValidationForm, ModelObjectiveValidationForm, \
            ModelParameterValidationForm, ModelOutputValidationForm, ExecutedByValidationForm
        super(SWATModelInstanceMetaData, self).update(metadata, user)
        attribute_mappings = {'modelobjective': 'model_objective',
                              'simulationtype': 'simulation_type',
                              'modelmethod': 'model_method',
                              'modelparameter': 'model_parameter',
                              'modelinput': 'model_input',
                              'modeloutput': 'model_output',
                              'executedby': 'executed_by'}
        validation_forms_mapping = {'modelobjective': ModelObjectiveValidationForm,
                                    'simulationtype': SimulationTypeValidationForm,
                                    'modelmethod': ModelMethodValidationForm,
                                    'modelparameter': ModelParameterValidationForm,
                                    'modelinput': ModelInputValidationForm,
                                    'modeloutput': ModelOutputValidationForm,
                                    'executedby': ExecutedByValidationForm}
        with transaction.atomic():
            # update/create non-repeatable element
            for element_name in attribute_mappings.keys():
                for dict_item in metadata:
                    if element_name in dict_item:
                        validation_form = validation_forms_mapping[element_name](
                            dict_item[element_name])
                        if not validation_form.is_valid():
                            err_string = self.get_form_errors_as_string(validation_form)
                            raise ValidationError(err_string)
                        element_property_name = attribute_mappings[element_name]
                        self.update_non_repeatable_element(element_name, metadata,
                                                           element_property_name)

    def get_xml(self, pretty_print=True, include_format_elements=True):

        # get the xml string representation of the core metadata elements
        xml_string = super(SWATModelInstanceMetaData, self).get_xml(pretty_print=pretty_print)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.model_objective:
            hsterms_model_objective = etree.SubElement(container,
                                                       '{%s}modelObjective'
                                                       % self.NAMESPACES['hsterms'])

            if self.model_objective.other_objectives:
                hsterms_model_objective.text = self.model_objective.get_swat_model_objectives() + \
                                               ', ' + self.model_objective.other_objectives
            else:
                hsterms_model_objective.text = self.model_objective.get_swat_model_objectives()
        if self.simulation_type:
            if self.simulation_type.simulation_type_name:
                hsterms_simulation_type = etree.SubElement(container, '{%s}simulationType'
                                                           % self.NAMESPACES['hsterms'])
                hsterms_simulation_type.text = self.simulation_type.simulation_type_name

        if self.model_method:
            modelMethodFields = ['runoffCalculationMethod', 'flowRoutingMethod',
                                 'petEstimationMethod']
            self.add_metadata_element_to_xml(container, self.model_method, modelMethodFields)

        if self.model_parameter:
            hsterms_swat_model_parameters = etree.SubElement(container, '{%s}modelParameter'
                                                             % self.NAMESPACES['hsterms'])

            if self.model_parameter.other_parameters:
                hsterms_swat_model_parameters.text = \
                    self.model_parameter.get_swat_model_parameters() + ', ' + \
                    self.model_parameter.other_parameters
            else:
                hsterms_swat_model_parameters.text = \
                    self.model_parameter.get_swat_model_parameters()

        if self.model_input:
            modelInputFields = ['warmupPeriodType', 'warmupPeriodValue', 'rainfallTimeStepType',
                                'rainfallTimeStepValue', 'routingTimeStepType',
                                'routingTimeStepValue', 'simulationTimeStepType',
                                'simulationTimeStepValue', 'watershedArea', 'numberOfSubbasins',
                                'numberOfHRUs', 'demResolution', 'demSourceName', 'demSourceURL',
                                'landUseDataSourceName', 'landUseDataSourceURL',
                                'soilDataSourceName', 'soilDataSourceURL'
                                ]
            self.add_metadata_element_to_xml(container, self.model_input, modelInputFields)

        return etree.tostring(RDF_ROOT, pretty_print=pretty_print)

    def delete_all_elements(self):
        super(SWATModelInstanceMetaData, self).delete_all_elements()
        self._model_objective.all().delete()
        self._simulation_type.all().delete()
        self._model_method.all().delete()
        self._model_parameter.all().delete()
        self._model_input.all().delete()
