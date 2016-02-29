__author__ = 'Mohamed Morsy'
from lxml import etree

from django.contrib.contenttypes import generic
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


# extended metadata elements for MODFLOW Model Instance resource type
class StudyArea(AbstractMetaDataElement):
    term = 'StudyArea'
    totalLength = models.CharField(max_length=100, null=True, blank=True,
                                   verbose_name='Study area total length in meters')
    totalWidth = models.CharField(max_length=100, null=True, blank=True,
                                  verbose_name='Study area total width in meters')
    maximumElevation = models.CharField(max_length=100, null=True, blank=True,
                                        verbose_name='Study area maximum elevation in meters')
    minimumElevation = models.CharField(max_length=100, null=True, blank=True,
                                        verbose_name='Study area minimum elevation in meters')

    def __unicode__(self):
        return self.totalLength

    class Meta:
        # StudyArea element is not repeatable
        unique_together = ("content_type", "object_id")


class GridDimensions(AbstractMetaDataElement):
    term = 'GridDimensions'
    gridTypeChoices = (('Regular', 'Regular'), ('Irregular', 'Irregular'),)

    numberOfLayers = models.CharField(max_length=100, null=True, blank=True, verbose_name='Number of model grid layers')
    typeOfRows = models.CharField(max_length=100, choices=gridTypeChoices, null=True, blank=True)
    numberOfRows = models.CharField(max_length=100, null=True, blank=True)
    typeOfColumns = models.CharField(max_length=100, choices=gridTypeChoices, null=True, blank=True)
    numberOfColumns = models.CharField(max_length=100, null=True, blank=True)

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

    stressPeriodType = models.CharField(max_length=100, choices=stressPeriodTypeChoices, null=True, blank=True)
    steadyStateValue = models.CharField(max_length=100, null=True, blank=True,
                                        verbose_name='Length of steady state stress period(s)')
    transientStateValueType = models.CharField(max_length=100, choices=transientStateValueTypeChoices, null=True)
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

    flowPackage = models.CharField(max_length=100, choices=flowPackageChoices, null=True, blank=True)
    flowParameter = models.CharField(max_length=100, choices=flowParameterChoices, null=True, blank=True)

    def __unicode__(self):
        return self.flowPackage

    class Meta:
        # GroundWaterFlow element is not repeatable
        unique_together = ("content_type", "object_id")


class BoundaryConditionTypeChoices(models.Model):
    description = models.CharField(max_length=300)


class BoundaryConditionPackageChoices(models.Model):
    description = models.CharField(max_length=300)


class BoundaryCondition(AbstractMetaDataElement):
    term = 'BoundaryCondition'
    boundaryConditionType = models.ManyToManyField(BoundaryConditionTypeChoices, null=True, blank=True)
    boundaryConditionPackage = models.ManyToManyField(BoundaryConditionPackageChoices, null=True, blank=True)

    # may be this could cause a problem
    def __unicode__(self):
        return self.boundaryConditionType

    class Meta:
        # BoundaryCondition element is not repeatable
        unique_together = ("content_type", "object_id")

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

    calibratedParameter = models.CharField(max_length=200, null=True, blank=True)
    observationType = models.CharField(max_length=200, null=True, blank=True)
    observationProcessPackage = models.CharField(max_length=100, choices=observationProcessPackageChoices, null=True,
                                                 blank=True)
    calibrationMethod = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        return self.calibratedParameter

    class Meta:
        # ModelCalibration element is not repeatable
        unique_together = ("content_type", "object_id")


class ModelInput(AbstractMetaDataElement):
    term = 'ModelInput'
    inputType = models.CharField(max_length=200, null=True, blank=True)
    inputSourceName = models.CharField(max_length=200, null=True, blank=True)
    inputSourceURL = models.URLField(null=True, blank=True, verbose_name='Input source URL')

    def __unicode__(self):
        return self.inputType


class GeneralElements(AbstractMetaDataElement):
    term = 'GeneralElements'
    modelSolverChoices = (('DE4', 'DE4'), ('GMG', 'GMG'), ('LMG', 'LMG'), ('PCG', 'PCG'),
                          ('PCGN', 'PCGN'), ('SIP', 'SIP'), ('SOR', 'SOR'), ('NWT', 'NWT'),)
    outputControlPackageChoices = (('GAGE', 'GAGE'), ('HYD', 'HYD'), ('LMT6', 'LMT6'), ('MNWI', 'MNWI'), ('OC', 'OC'),)
    subsidencePackageChoices = (('IBS', 'IBS'), ('SUB', 'SUB'), ('SWT', 'SWT'),)

    modelParameter = models.CharField(max_length=200, null=True, blank=True)
    modelSolver = models.CharField(max_length=100, choices=modelSolverChoices, null=True, blank=True)
    outputControlPackage = models.CharField(max_length=100, choices=outputControlPackageChoices, null=True, blank=True)
    subsidencePackage = models.CharField(max_length=100, choices=subsidencePackageChoices, null=True, blank=True)

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

    @classmethod
    def get_supported_upload_file_types(cls):
        # all file types are supported
        return ('.*')

    @classmethod
    def can_have_multiple_files(cls):
        return True

processor_for(MODFLOWModelInstanceResource)(resource_processor)


# metadata container class
class MODFLOWModelInstanceMetaData(ModelInstanceMetaData):
    _study_area = generic.GenericRelation(StudyArea)
    _grid_dimensions = generic.GenericRelation(GridDimensions)
    _stress_period = generic.GenericRelation(StressPeriod)
    _ground_water_flow = generic.GenericRelation(GroundWaterFlow)
    _boundary_condition = generic.GenericRelation(BoundaryCondition)
    _model_calibration = generic.GenericRelation(ModelCalibration)
    _model_input = generic.GenericRelation(ModelInput)
    _general_elements = generic.GenericRelation(GeneralElements)

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
    def model_input(self):
        return self._model_input.all().first()

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