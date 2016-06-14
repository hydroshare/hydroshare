__author__ = 'Mohamed Morsy'
from lxml import etree

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from mezzanine.pages.page_processors import processor_for

import os

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


# extended metadata elements for MODFLOW Model Instance resource type
class StudyArea(AbstractMetaDataElement):
    term = 'StudyArea'
    totalLength = models.CharField(max_length=100, null=True, blank=True,
                                   verbose_name='Total length in meters')
    totalWidth = models.CharField(max_length=100, null=True, blank=True,
                                  verbose_name='Total width in meters')
    maximumElevation = models.CharField(max_length=100, null=True, blank=True,
                                        verbose_name='Maximum elevation in meters')
    minimumElevation = models.CharField(max_length=100, null=True, blank=True,
                                        verbose_name='Minimum elevation in meters')

    def __unicode__(self):
        return self.totalLength

    class Meta:
        # StudyArea element is not repeatable
        unique_together = ("content_type", "object_id")


class GridDimensions(AbstractMetaDataElement):
    term = 'GridDimensions'
    gridTypeChoices = (('Regular', 'Regular'), ('Irregular', 'Irregular'),)

    numberOfLayers = models.CharField(max_length=100, null=True, blank=True,
                                      verbose_name='Number of layers')
    typeOfRows = models.CharField(max_length=100, choices=gridTypeChoices, null=True, blank=True,
                                  verbose_name='Type of rows')
    numberOfRows = models.CharField(max_length=100, null=True, blank=True,
                                    verbose_name='Number of rows')
    typeOfColumns = models.CharField(max_length=100, choices=gridTypeChoices, null=True, blank=True,
                                     verbose_name='Type of columns')
    numberOfColumns = models.CharField(max_length=100, null=True, blank=True,
                                       verbose_name='Number of columns')

    def __unicode__(self):
        return self.numberOfLayers

    class Meta:
        # GridDimensions element is not repeatable
        unique_together = ("content_type", "object_id")


class StressPeriod(AbstractMetaDataElement):
    term = 'StressPeriod'
    stressPeriodTypeChoices = (('Steady', 'Steady'), ('Transient', 'Transient'),
                               ('Steady and Transient', 'Steady and Transient'),)
    transientStateValueTypeChoices = (('Annually', 'Annually'), ('Monthly', 'Monthly'),
                                      ('Daily', 'Daily'), ('Hourly', 'Hourly'),)

    stressPeriodType = models.CharField(max_length=100, choices=stressPeriodTypeChoices, null=True, blank=True,
                                        verbose_name='Type')
    steadyStateValue = models.CharField(max_length=100, null=True, blank=True,
                                        verbose_name='Length of steady state stress period(s)')
    transientStateValueType = models.CharField(max_length=100, choices=transientStateValueTypeChoices, null=True,
                                               verbose_name='Type of transient state stress period(s)')
    transientStateValue = models.CharField(max_length=100, null=True, blank=True,
                                           verbose_name='Length of transient state stress period(s)')

    def __unicode__(self):
        return self.stressPeriodType

    class Meta:
        # StressPeriod element is not repeatable
        unique_together = ("content_type", "object_id")


class GroundWaterFlow(AbstractMetaDataElement):
    term = 'GroundWaterFlow'
    flowPackageChoices = (('BCF6', 'BCF6'), ('LPF', 'LPF'), ('HUF2', 'HUF2'),
                          ('UPW', 'UPW'), ('HFB6', 'HFB6'), ('UZF', 'UZF'), ('SWI2', 'SWI2'),)
    flowParameterChoices = (('Hydraulic Conductivity', 'Hydraulic Conductivity'),
                            ('Transmissivity', 'Transmissivity'),)

    flowPackage = models.CharField(max_length=100, choices=flowPackageChoices, null=True, blank=True,
                                   verbose_name='Flow package')
    flowParameter = models.CharField(max_length=100, choices=flowParameterChoices, null=True, blank=True,
                                     verbose_name='Flow parameter')

    def __unicode__(self):
        return self.flowPackage

    class Meta:
        # GroundWaterFlow element is not repeatable
        unique_together = ("content_type", "object_id")


class BoundaryConditionTypeChoices(models.Model):
    description = models.CharField(max_length=300)

    def __unicode__(self):
        return self.description


class BoundaryConditionPackageChoices(models.Model):
    description = models.CharField(max_length=300)

    def __unicode__(self):
        return self.description


class BoundaryCondition(AbstractMetaDataElement):
    term = 'BoundaryCondition'
    boundaryConditionType = models.ManyToManyField(BoundaryConditionTypeChoices, null=True, blank=True)
    boundaryConditionPackage = models.ManyToManyField(BoundaryConditionPackageChoices, null=True, blank=True)

    # may be this could cause a problem
    def __unicode__(self):
        return self.term

    class Meta:
        # BoundaryCondition element is not repeatable
        unique_together = ("content_type", "object_id")

    def get_boundary_condition_type(self):
        return ', '.join([types.description for types in self.boundaryConditionType.all()])

    def get_boundary_condition_package(self):
        return ', '.join([packages.description for packages in self.boundaryConditionPackage.all()])

    @classmethod
    def _add_boundary_types(cls, boundary_choices, choices):
        for type_choices in choices:
            qs = BoundaryConditionTypeChoices.objects.filter(description__exact=type_choices)
            if qs.exists():
                boundary_choices.boundaryConditionType.add(qs[0])
            else:
                boundary_choices.boundaryConditionType.create(description=type_choices)

    @classmethod
    def _add_boundary_packages(cls, boundary_packages, packages):
        for package in packages:
            qs = BoundaryConditionPackageChoices.objects.filter(description__exact=package)
            if qs.exists():
                boundary_packages.boundaryConditionPackage.add(qs[0])
            else:
                boundary_packages.boundaryConditionPackage.create(description=package)

    # need to define create and update methods
    @classmethod
    def create(cls, **kwargs):
        if 'boundaryConditionType' in kwargs:
            cls._validate_boundary_condition_types(kwargs['boundaryConditionType'])
        else:
            raise ValidationError("boundaryConditionType is missing.")
        if 'boundaryConditionPackage' in kwargs:
            cls._validate_boundary_condition_packages(kwargs['boundaryConditionPackage'])
        else:
            raise ValidationError("boundaryConditionPackage is missing.")
        model_boundary_condition = super(BoundaryCondition, cls).create(content_object=kwargs['content_object'])
        cls._add_boundary_types(model_boundary_condition, kwargs['boundaryConditionType'])
        cls._add_boundary_packages(model_boundary_condition, kwargs['boundaryConditionPackage'])

        return model_boundary_condition

    @classmethod
    def update(cls, element_id, **kwargs):
        model_boundary_condition = BoundaryCondition.objects.get(id=element_id)
        if model_boundary_condition:
            if 'boundaryConditionType' in kwargs:
                cls._validate_boundary_condition_types(kwargs['boundaryConditionType'])
                # delete ManyToMany associated records
                model_boundary_condition.boundaryConditionType.clear()
                cls._add_boundary_types(model_boundary_condition, kwargs['boundaryConditionType'])

            if 'boundaryConditionPackage' in kwargs:
                cls._validate_boundary_condition_packages(kwargs['boundaryConditionPackage'])
                # delete ManyToMany associated records
                model_boundary_condition.boundaryConditionPackage.clear()
                cls._add_boundary_packages(model_boundary_condition, kwargs['boundaryConditionPackage'])

            model_boundary_condition.save()

            # delete boundaryConditionType and boundaryConditionPackage elements if it has no data
            if len(model_boundary_condition.boundaryConditionType.all()) == 0 and\
               len(model_boundary_condition.boundaryConditionPackage.all()) == 0:
                model_boundary_condition.delete()
        else:
            raise ObjectDoesNotExist("No BoundaryCondition element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def _validate_boundary_condition_types(cls, types):
        for boundary_types in types:
            if boundary_types not in ['Specified Head Boundaries', 'Specified Flux Boundaries',
                                      'Head-Dependent Flux Boundary']:
                raise ValidationError('Invalid Boundary Condition Type:%s' % types)

    @classmethod
    def _validate_boundary_condition_packages(cls, packages):
        for boundary_packages in packages:
            if boundary_packages not in ['BFH', 'CHD', 'FHB', 'RCH', 'WEL', 'DAF', 'DAFG', 'DRN', 'DRT', 'ETS', 'EVT',
                                         'GHB', 'LAK', 'MNW1', 'MNW2', 'RES', 'RIP', 'RIV', 'SFR', 'STR', 'UZF']:
                raise ValidationError('Invalid Boundary Condition Type:%s' % packages)


class ModelCalibration(AbstractMetaDataElement):
    term = 'ModelCalibration'
    observationProcessPackageChoices = (('ADV2', 'ADV2'), ('CHOB', 'CHOB'), ('DROB', 'DROB'),
                                        ('DTOB', 'DTOB'), ('GBOB', 'GBOB'), ('HOB', 'HOB'),
                                        ('OBS', 'OBS'), ('RVOB', 'RVOB'), ('STOB', 'STOB'),)

    calibratedParameter = models.CharField(max_length=200, null=True, blank=True,
                                           verbose_name='Calibrated parameter(s)')
    observationType = models.CharField(max_length=200, null=True, blank=True, verbose_name='Observation type(s)')
    observationProcessPackage = models.CharField(max_length=100, choices=observationProcessPackageChoices, null=True,
                                                 blank=True, verbose_name='Observation process package')
    calibrationMethod = models.CharField(max_length=200, null=True, blank=True, verbose_name='Calibration method(s)')

    def __unicode__(self):
        return self.calibratedParameter

    class Meta:
        # ModelCalibration element is not repeatable
        unique_together = ("content_type", "object_id")


class ModelInput(AbstractMetaDataElement):
    term = 'ModelInput'
    inputType = models.CharField(max_length=200, null=True, blank=True, verbose_name='Type')
    inputSourceName = models.CharField(max_length=200, null=True, blank=True, verbose_name='Source name')
    inputSourceURL = models.URLField(null=True, blank=True, verbose_name='Source URL')

    def __unicode__(self):
        return self.inputType


class GeneralElements(AbstractMetaDataElement):
    term = 'GeneralElements'
    modelSolverChoices = (('DE4', 'DE4'), ('GMG', 'GMG'), ('LMG', 'LMG'), ('PCG', 'PCG'),
                          ('PCGN', 'PCGN'), ('SIP', 'SIP'), ('SOR', 'SOR'), ('NWT', 'NWT'),)
    outputControlPackageChoices = (('GAGE', 'GAGE'), ('HYD', 'HYD'), ('LMT6', 'LMT6'), ('MNWI', 'MNWI'), ('OC', 'OC'),)
    subsidencePackageChoices = (('IBS', 'IBS'), ('SUB', 'SUB'), ('SWT', 'SWT'),)

    modelParameter = models.CharField(max_length=200, null=True, blank=True, verbose_name='Model parameter(s)')
    modelSolver = models.CharField(max_length=100, choices=modelSolverChoices, null=True, blank=True,
                                   verbose_name='Model solver')
    outputControlPackage = models.CharField(max_length=100, choices=outputControlPackageChoices, null=True, blank=True,
                                            verbose_name='Output control package')
    subsidencePackage = models.CharField(max_length=100, choices=subsidencePackageChoices, null=True, blank=True,
                                         verbose_name='Subsidence package')

    def __unicode__(self):
        return self.modelParameter

    class Meta:
        # GeneralElements element is not repeatable
        unique_together = ("content_type", "object_id")


# MODFLOW Model Instance Resource type
class MODFLOWModelInstanceResource(BaseResource):
    objects = ResourceManager("MODFLOWModelInstanceResource")

    class Meta:
        verbose_name = 'MODFLOW Model Instance Resource'
        proxy = True

    @property
    def metadata(self):
        md = MODFLOWModelInstanceMetaData()
        return self._get_metadata(md)

    def has_required_content_files(self):
        if self.files.all().count() >= 1:
            files = self.find_content_files()
            if files[0] != 1:
                return False
            else:
                for f in files[1]:
                    if f not in files[2]:
                        return False
                else:
                    return True
        else:
            return False

    def check_content_files(self):
        missing_files = []
        if self.files.all().count() >= 1:
            files = self.find_content_files()
            if not files[0]:
                return ['.nam']
            else:
                if files[0] > 1:
                    return 'multiple_nam'
                else:
                    for f in files[1]:
                        if f not in files[2]:
                            missing_files.append(f)
                    return missing_files
        else:
            return ['.nam']

    def find_content_files(self):
        nam_file_count = 0
        existing_files = []
        reqd_files = []
        for res_file in self.files.all():
                ext = os.path.splitext(res_file.resource_file.name)[-1]
                existing_files.append(res_file.resource_file.name.split("/")[-1])
                if ext == '.nam':
                    nam_file_count += 1
                    name_file = res_file.resource_file.file
                    for rows in name_file:
                        rows = rows.strip()
                        rows = rows.split(" ")
                        r = rows[0].strip()
                        if r != '#' and r != '' and r.lower() != 'list' and r.lower() != 'data' \
                                and r.lower() != 'data(binary)':
                            reqd_files.append(rows[-1].strip())
        return nam_file_count, reqd_files, existing_files


processor_for(MODFLOWModelInstanceResource)(resource_processor)


# metadata container class
class MODFLOWModelInstanceMetaData(ModelInstanceMetaData):
    _study_area = GenericRelation(StudyArea)
    _grid_dimensions = GenericRelation(GridDimensions)
    _stress_period = GenericRelation(StressPeriod)
    _ground_water_flow = GenericRelation(GroundWaterFlow)
    _boundary_condition = GenericRelation(BoundaryCondition)
    _model_calibration = GenericRelation(ModelCalibration)
    _model_input = GenericRelation(ModelInput)
    _general_elements = GenericRelation(GeneralElements)

    @property
    def study_area(self):
        return self._study_area.all().first()

    @property
    def grid_dimensions(self):
        return self._grid_dimensions.all().first()

    @property
    def stress_period(self):
        return self._stress_period.all().first()

    @property
    def ground_water_flow(self):
        return self._ground_water_flow.all().first()

    @property
    def boundary_condition(self):
        return self._boundary_condition.all().first()

    @property
    def model_calibration(self):
        return self._model_calibration.all().first()

    @property
    def model_inputs(self):
        return self._model_input.all()

    @property
    def general_elements(self):
        return self._general_elements.all().first()

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(MODFLOWModelInstanceMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('StudyArea')
        elements.append('GridDimensions')
        elements.append('StressPeriod')
        elements.append('GroundWaterFlow')
        elements.append('BoundaryCondition')
        elements.append('ModelCalibration')
        elements.append('ModelInput')
        elements.append('GeneralElements')
        return elements

    def has_all_required_elements(self):
        if not super(MODFLOWModelInstanceMetaData, self).has_all_required_elements():
            return False
        return True

    def get_xml(self, pretty_print=True):
        # get the xml string representation of the core metadata elements
        xml_string = super(MODFLOWModelInstanceMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.study_area:
            studyAreaFields = ['totalLength', 'totalWidth', 'maximumElevation', 'minimumElevation']
            self.add_metadata_element_to_xml(container, self.study_area, studyAreaFields)

        if self.grid_dimensions:
            gridDimensionsFields = ['numberOfLayers', 'typeOfRows', 'numberOfRows', 'typeOfColumns', 'numberOfColumns']
            self.add_metadata_element_to_xml(container, self.grid_dimensions, gridDimensionsFields)

        if self.stress_period:
            stressPeriodFields = ['stressPeriodType', 'steadyStateValue',
                                  'transientStateValueType', 'transientStateValue']
            self.add_metadata_element_to_xml(container, self.stress_period, stressPeriodFields)

        if self.ground_water_flow:
            groundWaterFlowFields = ['flowPackage', 'flowParameter']
            self.add_metadata_element_to_xml(container, self.ground_water_flow, groundWaterFlowFields)

        if self.boundary_condition:
            hsterms_boundary = etree.SubElement(container, '{%s}BoundaryCondition' % self.NAMESPACES['hsterms'])
            hsterms_boundary_rdf_Description = etree.SubElement(hsterms_boundary, '{%s}Description' % self.NAMESPACES['rdf'])

            if self.boundary_condition.boundaryConditionType:
                hsterms_boundary_type = etree.SubElement(hsterms_boundary_rdf_Description, '{%s}boundaryConditionType' % self.NAMESPACES['hsterms'])
                hsterms_boundary_type.text = ', '.join([types.description for types in self.boundary_condition.boundaryConditionType.all()])

            if self.boundary_condition.boundaryConditionPackage:
                hsterms_boundary_package = etree.SubElement(hsterms_boundary_rdf_Description, '{%s}boundaryConditionType' % self.NAMESPACES['hsterms'])
                hsterms_boundary_package.text = ', '.join([packages.description for packages in self.boundary_condition.boundaryConditionPackage.all()])

        if self.model_calibration:
            modelCalibrationFields = ['calibratedParameter', 'observationType',
                                      'observationProcessPackage', 'calibrationMethod']
            self.add_metadata_element_to_xml(container, self.model_calibration, modelCalibrationFields)

        if self.model_inputs:
            modelInputFields = ['inputType', 'inputSourceName', 'inputSourceURL']
            self.add_metadata_element_to_xml(container, self.model_inputs.first(), modelInputFields)

        if self.general_elements:

            if self.general_elements.modelParameter:
                model_parameter = etree.SubElement(container, '{%s}modelParameter' % self.NAMESPACES['hsterms'])
                model_parameter.text = self.general_elements.modelParameter

            if self.general_elements.modelSolver:
                model_solver = etree.SubElement(container, '{%s}modelSolver' % self.NAMESPACES['hsterms'])
                model_solver.text = self.general_elements.modelSolver

            if self.general_elements.outputControlPackage:
                output_package = etree.SubElement(container, '{%s}outputControlPackage' % self.NAMESPACES['hsterms'])
                output_package.text = self.general_elements.outputControlPackage

            if self.general_elements.subsidencePackage:
                subsidence_package = etree.SubElement(container, '{%s}subsidencePackage' % self.NAMESPACES['hsterms'])
                subsidence_package.text = self.general_elements.subsidencePackage

        return etree.tostring(RDF_ROOT, pretty_print=True)

    def delete_all_elements(self):
        super(MODFLOWModelInstanceMetaData, self).delete_all_elements()
        self._study_area.all().delete()
        self._grid_dimensions.all().delete()
        self._stress_period.all().delete()
        self._ground_water_flow.all().delete()
        self._boundary_condition.all().delete()
        self._model_calibration.all().delete()
        self._model_input.all().delete()
        self._general_elements.all().delete()

import receivers
