from lxml import etree

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, AbstractMetaDataElement
# from hs_core.hydroshare import utils

from hs_model_program.models import ModelProgramResource
from hs_modelinstance.models import ModelInstanceMetaData, ModelOutput, ExecutedBy

MODEL_INPUT_FIELDS = ['rainfall_type_choices', 'routing_type_choices', 'rainfallTimeStepType',
                      'routingTimeStepType', 'watershedArea', 'numberOfSubbasins',
                      'demResolution', 'demSourceName', 'demSourceURL',
                      'landCoverDataSourceName', 'landCoverDataSourceURL',
                      'soilDataSourceName', 'soilDataSourceURL']

class ModelInput(AbstractMetaDataElement):
    term = 'ModelInput'
    rainfall_type_choices = (('Daily', 'Daily'), ('Hourly', 'Hourly'), ('Hourly and Daily', 'Hourly and Daily'))
    routing_type_choices = (('Spatial', 'Spatial'), ('TOPMODEL', 'TOPMODEL'),)

    rainfallTimeStepType = models.CharField(max_length=100, choices=rainfall_type_choices, null=True, blank=True,
                                            verbose_name='Rainfall time step type')
    routingTimeStepType = models.CharField(max_length=100, choices=routing_type_choices, null=True, blank=True,
                                           verbose_name='Routing time step type')

    watershedArea = models.CharField(max_length=100, null=True, blank=True,
                                     verbose_name='Watershed area in square kilometers')
    numberOfSubbasins = models.CharField(max_length=100, null=True, blank=True, verbose_name='Number of sub basins')

    demResolution = models.CharField(max_length=100, null=True, blank=True, verbose_name='DEM resolution in meters')
    demSourceName = models.CharField(max_length=200, null=True, blank=True, verbose_name='DEM source name')
    demSourceURL = models.URLField(null=True, blank=True, verbose_name='DEM source URL')
    landCoverDataSourceName = models.CharField(max_length=200, null=True, blank=True,
                                               verbose_name='Land cover data source name')
    landCoverDataSourceURL = models.URLField(null=True, blank=True, verbose_name='Land cover data source URL')
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


class RHESSysModelInstanceresource(BaseResource):
    objects = ResourceManager("RHESSysModelInstanceResource")

    class Meta:
        verbose_name = 'RHESSys Model Instance Resource'
        proxy = True

    @property
    def metadata(self):
        md = RHESSysModelInstanceMetaData()
        return self._get_metadata(md)

    @classmethod
    def get_supported_upload_file_types(cls):
        # RHESSys models must be encapsulated in a zip file.
        return '.zip'

    @classmethod
    def can_have_multiple_files(cls):
        return True

processor_for(RHESSysModelInstanceresource)(resource_processor)


class RHESSysModelInstanceMetaData(ModelInstanceMetaData):
    _model_input = GenericRelation(ModelInput)

    @property
    def model_input(self):
        return self._model_input.all().first()

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(RHESSysModelInstanceMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        # elements.append('ModelObjective')
        # elements.append('SimulationType')
        # elements.append('ModelMethod')
        # elements.append('ModelParameter')
        elements.append('ModelInput')
        return elements

    def has_all_required_elements(self):
        if not super(RHESSysModelInstanceMetaData, self).has_all_required_elements():
            return False
        if not self.model_objective:
            return False
        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(RHESSysModelInstanceMetaData, self).get_required_missing_elements()
        if not self.model_objective:
            missing_required_elements.append('ModelObjective')
        return missing_required_elements

    def get_xml(self, pretty_print=True):

        # get the xml string representation of the core metadata elements
        xml_string = super(RHESSysModelInstanceMetaData, self).get_xml(pretty_print=pretty_print)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.model_input:
            self.add_metadata_element_to_xml(container, self.model_input, MODEL_INPUT_FIELDS)

        return etree.tostring(RDF_ROOT, pretty_print=True)

    def delete_all_elements(self):
        super(RHESSysModelInstanceMetaData, self).delete_all_elements()
        # self._model_objective.all().delete()
        # self._simulation_type.all().delete()
        # self._model_method.all().delete()
        # self._model_parameter.all().delete()
        self._model_input.all().delete()